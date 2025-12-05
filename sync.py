import typer, time, os, pandas as pd
from sqlalchemy import create_engine, text
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

app = typer.Typer(help="Live two-way Excel ↔ Database sync")

def excel_to_db(excel_path: str, engine, table_name: str):
    if not os.path.exists(excel_path):
        typer.echo(f"Excel file {excel_path} not found!")
        return False

    df = pd.read_excel(excel_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    typer.echo(f"Excel → DB sync complete ({len(df)} rows)")
    return True

def db_to_excel(engine, table_name: str, excel_path: str):
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        df.to_excel(excel_path, index=False)
        typer.echo(f"DB → Excel sync complete ({len(df)} rows)")
    except:
        pass  # Table might not exist yet

class ExcelHandler(FileSystemEventHandler):
    def __init__(self, excel_path, engine, table_name):
        self.excel_path = excel_path
        self.engine = engine
        self.table_name = table_name
        self.lock = threading.Lock()

    def on_modified(self, event):
        if event.src_path.endswith(os.path.basename(self.excel_path)):
            with self.lock:
                time.sleep(0.5)  # Wait for file save
                excel_to_db(self.excel_path, self.engine, self.table_name)

@app.command()
def sync(
    excel: str = typer.Argument(..., help="Path to Excel file"),
    db: str = typer.Option("sqlite:///sync.db", "--db", help="Database URL"),
    table: str = typer.Option(None, "--table", help="Table name (default: filename)")
):
    """Start live two-way sync"""
    table = table or os.path.splitext(os.path.basename(excel))[0].lower()
    engine = create_engine(db)

    # Initial sync
    excel_to_db(excel, engine, table)

    # Start watcher
    event_handler = ExcelHandler(excel, engine, table)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(excel) or ".", recursive=False)
    observer.start()

    typer.echo(f"Live sync started: {excel} ↔ {table}")
    typer.echo("Press Ctrl+C to stop")

    # Keep DB → Excel updated every 10 seconds
    def db_watcher():
        last_hash = None
        while True:
            try:
                current = pd.read_sql(f"SELECT COUNT(*) FROM {table}", engine).iloc[0,0]
                if last_hash != current:
                    db_to_excel(engine, table, excel)
                    last_hash = current
            except:
                pass
            time.sleep(10)

    threading.Thread(target=db_watcher, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        typer.echo("Sync stopped")
    observer.join()

if __name__ == "__main__":
    app()
