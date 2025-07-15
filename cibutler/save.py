from rich.console import Console
import cibutler.utils as utils
import pandas
from pandas.core.groupby.groupby import DataError
import typer
import logging

logger = logging.getLogger(__name__)

console = Console()
error_console = Console(stderr=True, style="bold red")


def save_results_pandas(
    data,
    filename_prefix,
    sheet_name="Search Results",
    normalize=True,
    index=True,
    output=utils.OutputType.excel,
    record_path="results",
):
    if output == utils.OutputType.excel:
        filename = f"{filename_prefix}.xlsx"
    else:
        filename = f"{filename_prefix}.csv"

    try:
        if normalize:
            if record_path:
                df = pandas.json_normalize(data, record_path=[record_path])
            else:
                df = pandas.json_normalize(data)
        else:
            df = pandas.DataFrame(data[record_path])

        if output == utils.OutputType.excel:
            with pandas.ExcelWriter(filename) as writer:
                df.to_excel(writer, index=index, sheet_name=sheet_name)
        else:
            df.to_csv(filename, index=False)

    except DataError as e:
        error_console.print(f"Error: unable to save to {filename} {e}")
        raise typer.Exit(1)  # non-zero exit status

    console.print(f"Search results saved as '{filename}'")
