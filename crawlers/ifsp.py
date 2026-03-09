import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

class IFSPCourseScraper:
    def __init__(self):
        self.base_url = "https://www.ifsp.edu.br"
        self.start_url = urljoin(self.base_url, "index.php/cursos")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_soup(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def run(self):
        print(f"Iniciando captura em: {self.start_url}")
        main_soup = self.fetch_soup(self.start_url)
        categories = self._extract_categories(main_soup)
        
        full_data = {}
        
        for category_name, category_url in categories.items():
            print(f"Navegando em categoria: {category_name}")
            courses = self._scrape_category_page(category_url)
            full_data[category_name] = courses
            
        return full_data

    def _extract_categories(self, soup):
        categories = {}
        content_area = soup.find("div", class_="item-page")
        if not content_area:
            return categories

        # Localiza links que apontam para subpáginas de cursos
        # Adicionada verificação rigorosa de 'href'
        links = content_area.find_all("a", href=True)
        for link in links:
            href = link.get("href")
            
            # Filtra apenas links de interesse e ignora âncoras vazias
            if href and ("id=" in href or "article" in href):
                name = link.get_text(strip=True)
                if name and len(name) > 3:
                    categories[name] = urljoin(self.base_url, href)
        
        return categories

    def _scrape_category_page(self, url):
        try:
            soup = self.fetch_soup(url)
        except Exception as error:
            print(f"Aviso: Falha ao acessar {url}. Erro: {error}")
            return []

        course_list = []
        # O conteúdo útil no Joomla/K2 do IFSP geralmente está aqui
        content = soup.find("div", class_="item-page")
        
        if content:
            # Captura elementos de lista ou células de tabela
            items = content.find_all(["li", "td", "p"])
            for item in items:
                link = item.find("a", href=True)
                if link:
                    course_name = link.get_text(strip=True)
                    course_href = link.get("href")
                    
                    # Evita capturar links de navegação "Anterior/Próximo" ou vazios
                    if course_name and len(course_name) > 5 and "index.php/cursos" not in course_href:
                        course_url = urljoin(self.base_url, course_href)
                        if course_url not in [c['url'] for c in course_list]:
                            course_list.append({
                                "name": course_name,
                                "url": course_url
                            })
                else:
                    text = item.get_text(strip=True)
                    # Se não houver link, mas houver texto relevante, salva como informação
                    if text and 10 < len(text) < 100:
                        if not any(c['name'] == text for c in course_list):
                            course_list.append({"name": text, "url": None})

        return course_list

    def save_results(self, data, filename="courses_ifsp.json"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"Processo finalizado. {sum(len(v) for v in data.values())} itens salvos em {filename}")

if __name__ == "__main__":
    scraper = IFSPCourseScraper()
    try:
        results = scraper.run()
        scraper.save_results(results)
    except Exception as error:
        print(f"Erro crítico durante a execução: {error}")