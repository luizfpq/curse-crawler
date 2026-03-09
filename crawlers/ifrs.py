import requests
from bs4 import BeautifulSoup
import json

class IFRSCourseScraper:
    def __init__(self):
        self.url = "https://estude.ifrs.edu.br/cursos"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch_html(self):
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def parse_courses(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        course_data = []

        # Localiza as seções de cada campus
        campus_sections = soup.find_all("div", class_="cursos__unidade")

        for section in campus_sections:
            campus_name = self._extract_campus_name(section)
            courses = section.find_all("article", class_="curso-item")

            for course in courses:
                course_info = self._extract_course_details(course, campus_name)
                course_data.append(course_info)

        return course_data

    def _extract_campus_name(self, section):
        title_element = section.find("h3", class_="cursos__unidade-title")
        if title_element:
            # Remove textos auxiliares de acessibilidade
            return title_element.get_text(strip=True).replace("Cursos em", "").strip()
        return "Não identificado"

    def _extract_course_details(self, course, campus_name):
        title_element = course.find("h4", class_="curso-item__title")
        level_element = course.find("p", class_="curso-item__nivel")
        
        # Metadados: carga horária, turno, modalidade
        meta_spans = course.find_all("span", class_=lambda x: x and x.startswith("curso-item__meta--"))
        
        details = {
            "campus": campus_name,
            "title": title_element.get_text(strip=True) if title_element else "",
            "url": title_element.find("a")["href"] if title_element and title_element.find("a") else "",
            "level": level_element.get_text(strip=True) if level_element else "",
        }

        for span in meta_spans:
            class_name = span["class"][0]
            content = span.get_text(strip=True)
            
            if "cargahoraria" in class_name:
                details["duration"] = content
            elif "turnos" in class_name:
                details["shifts"] = content
            elif "modalidades" in class_name:
                details["modality"] = content

        return details

    def save_to_json(self, data, filename="json/courses_ifrs.json"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"Sucesso: {len(data)} cursos capturados e salvos em {filename}")

if __name__ == "__main__":
    scraper = IFRSCourseScraper()
    try:
        html = scraper.fetch_html()
        courses = scraper.parse_courses(html)
        scraper.save_to_json(courses)
    except Exception as error:
        print(f"Erro ao processar a página: {error}")