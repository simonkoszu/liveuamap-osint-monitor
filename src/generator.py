import os
import shutil
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

class ReportGenerator:
    """
    Generator raportu HTML:
    - Renderuje szablon Jinja2 z danymi analitycznymi, mapą i wykresami
    - Zapisuje lokalny plik w katalogu output/
    - Opcjonalnie kopiuje raport do folderu na Pulpicie użytkownika
    """
    def __init__(self, templates_dir: str, output_dir: str):
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True
        )

    def generate(self, data: Dict[str, Any], desktop_folder_name: str = "liveuamap_raport") -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        template = self.env.get_template("report_template.html")
        html_content = template.render(data=data)

        # 1. Zapis w folderze projektu output/index.html
        output_file = os.path.join(self.output_dir, "index.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[GENERATOR] Raport HTML zapisany pomyślnie w: {output_file}")

        # 2. Zapis w folderze na Pulpicie (Desktop) zgodnie z poleceniem użytkownika
        desktop_dir = os.path.expanduser(f"~/Desktop/{desktop_folder_name}")
        try:
            os.makedirs(desktop_dir, exist_ok=True)
            desktop_file = os.path.join(desktop_dir, "index.html")
            shutil.copyfile(output_file, desktop_file)
            print(f"[GENERATOR] Kopia raportu zapisana na Pulpicie: {desktop_file}")
        except Exception as e:
            print(f"[GENERATOR] Uwaga: Nie udało się skopiować na Pulpit: {e}")

        return output_file
