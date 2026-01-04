"""
Script simple para analizar la página de AgentesNet usando requests
"""

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explorar():
    url = "https://www.agentesbet.net/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"Fetching: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        print(f"Status: {response.status_code}")
        print(f"URL final: {response.url}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar formularios
            forms = soup.find_all('form')
            print(f"\n=== Formularios encontrados: {len(forms)} ===")
            for i, form in enumerate(forms):
                print(f"\nForm {i}:")
                print(f"  Action: {form.get('action')}")
                print(f"  Method: {form.get('method')}")

            # Buscar inputs
            inputs = soup.find_all('input')
            print(f"\n=== Inputs encontrados: {len(inputs)} ===")
            for inp in inputs:
                print(f"  type={inp.get('type')}, name={inp.get('name')}, placeholder={inp.get('placeholder')}")

            # Buscar botones
            buttons = soup.find_all(['button', 'input[type="submit"]'])
            print(f"\n=== Botones encontrados: {len(buttons)} ===")
            for btn in buttons:
                print(f"  {btn.name}: {btn.get_text(strip=True)} | class={btn.get('class')}")

            # Guardar HTML para inspección
            with open('pagina_login.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\nHTML guardado en: pagina_login.html")

        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    explorar()
