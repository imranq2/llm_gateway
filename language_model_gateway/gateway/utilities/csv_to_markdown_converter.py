import csv
from io import StringIO
from typing import List


class CsvToMarkdownConverter:
    @staticmethod
    def csv_to_markdown_table(
        csv_string: str,
        delimiter: str = ",",
        quote_char: str = '"',
        has_header: bool = True,
    ) -> str:
        """
        Convert a CSV string to a Markdown table, handling quoted fields.

        Args:
            csv_string (str): The input CSV string
            delimiter (str, optional): CSV delimiter. Defaults to ','.
            quote_char (str, optional): Quote character. Defaults to '"'.
            has_header (bool, optional): Whether the first row is a header. Defaults to True.

        Returns:
            str: Markdown formatted table
        """
        # Normalize input string and strip whitespace
        csv_string = csv_string.strip()

        # Use StringIO to make the CSV string file-like
        csv_file = StringIO(csv_string)

        # Use csv reader with quote handling
        csv_reader = csv.reader(
            csv_file,
            delimiter=delimiter,
            quotechar=quote_char,
            skipinitialspace=True,  # Ignore spaces after delimiter
        )

        # Convert rows to list for processing
        try:
            rows = list(csv_reader)
        except csv.Error as e:
            return f"Error parsing CSV: {str(e)}"

        if not rows:
            return "| No Data |"

        # Separate headers and data rows
        headers = (
            rows[0] if has_header else [f"Column {i + 1}" for i in range(len(rows[0]))]
        )
        data_rows = rows[1:] if has_header else rows

        # Escape Markdown special characters in cells
        def escape_markdown_chars(cell: str) -> str:
            """Escape characters that have special meaning in Markdown tables."""
            return cell.replace("|", "\\|")

        # Create Markdown table
        # noinspection PyListCreation
        markdown_lines: List[str] = []

        # Header row
        markdown_lines.append(
            "| "
            + " | ".join(escape_markdown_chars(str(header)) for header in headers)
            + " |"
        )

        # Separator row with alignment
        markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Data rows
        for row in data_rows:
            markdown_lines.append(
                "| "
                + " | ".join(escape_markdown_chars(str(cell)) for cell in row)
                + " |"
            )

        return "\n".join(markdown_lines)
