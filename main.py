import pandas as pd
import requests
from bs4 import BeautifulSoup

def scrapeTables(urlStartingGrid, urlRaceResult) -> list:
    location = urlRaceResult.split("/")[8].replace("-", " ").capitalize()
    isSprint = "Yes" if "sprint-grid" in urlStartingGrid else "No"

    rspStartingGrid = requests.get(urlStartingGrid)
    rspRaceResult = requests.get(urlRaceResult)

    if rspRaceResult.status_code != 200 or rspStartingGrid.status_code != 200:
        print(f"        Página no encontrada en: {urlStartingGrid} y/o {urlRaceResult}")
        return []

    soupStartingGrid = BeautifulSoup(rspStartingGrid.text, 'html.parser')
    soupRaceResult = BeautifulSoup(rspRaceResult.text, 'html.parser')

    tableStartingGrid = soupStartingGrid.find("table", class_="f1-table f1-table-with-data w-full")
    tableRaceResult = soupRaceResult.find("table", class_="f1-table f1-table-with-data w-full")

    if tableStartingGrid is None or tableRaceResult is None:
        print(f"        Tabla no encontrada en: {urlStartingGrid} y/o {urlRaceResult}")
        return []

    print(f"        Recolectando datos de: {urlStartingGrid} y {urlRaceResult}")

    raceData = {}

    # starting grid
    for row in tableStartingGrid.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 4:
            no = cols[1].text.strip()

            raceData[no] = {
                "Year": urlRaceResult.split('/')[5],
                "Location": location,
                "Is Sprint": isSprint,
                "No": no,
                "Starting Pos": cols[0].text.strip(),
                "Final Pos": "n/d",
                "Driver": cols[2].text.strip()[:-3],
                "Car": cols[3].text.strip(),
            }

    # race result
    for row in tableRaceResult.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) >= 7:
            no = cols[1].text.strip()

            if no in raceData:  # Si el corredor está registrado
                raceData[no]["Final Pos"] = cols[0].text.strip()
            else:
                raceData[no] = {
                    "Year": urlRaceResult.split('/')[5],
                    "Location": location,
                    "Is Sprint": isSprint,
                    "No": no,
                    "Starting Pos": "n/d",
                    "Final Pos": cols[0].text.strip(),
                    "Driver": cols[2].text.strip()[:-3],
                    "Car": cols[3].text.strip(),
                }

    return list(raceData.values())


def getAllYears(url) -> list:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    yearsHtml = soup.find("ul", class_="f1-menu-wrapper")

    if yearsHtml:
        return [li["data-value"] for li in yearsHtml.find_all("li", {"data-name": "year"})]
    else:
        return []


def getLocationId(url) -> list:
    response = requests.get(url)

    if response.status_code != 200:
        print("Error al obtener la pagina")
        exit(1)

    soupPaisId = BeautifulSoup(response.text, 'html.parser')
    tablaPaises = soupPaisId.find_all("ul", class_="f1-menu-wrapper")[2]

    if tablaPaises:
        return [(li["data-value"], li["data-id"]) for li in tablaPaises.find_all("li", {"data-name": "races"})]
    else:
        return []


def getInputInt(mensaje):
    while True:
        try:
            year = int(input(mensaje))
            return year
        except ValueError:
            print("Por favor, ingrese un input válido.")


def recolectarDatos(yearsList, url):

    print("Iniciando recolección...")

    data = []

    for year in yearsList:
        print(f"\nRecolección de datos para el año {year}...")

        url1 = "/".join(url.split("/")[:5]) + "/"
        url2 = "/" + "/".join(url.split("/")[6:])
        mainUrl = url1 + str(year) + url2

        locationIdList = getLocationId(mainUrl)

        # Recolectar datos de cada carrera
        for location, idPais in locationIdList:
            print(f"    Recolectando datos de {location.replace('-', ' ').capitalize()}...")

            raseResult = mainUrl + f"/{idPais}/{location}/race-result"
            startingGrid = mainUrl + f"/{idPais}/{location}/starting-grid"

            data.extend(scrapeTables(startingGrid, raseResult))

            # por si tienen sprint
            sprint = mainUrl + f"/{idPais}/{location}/sprint-results"
            sprintGrid = mainUrl + f"/{idPais}/{location}/sprint-grid"

            data.extend(scrapeTables(sprintGrid, sprint))

    return data


if __name__ == "__main__":
    urlMain = f"https://www.formula1.com/en/results/2025/races"

    ##### INTERFAZ #####
    print("-" * 20)
    print("FORMULA1 SCRAPER")
    print("-" * 20)

    eleccion = 0
    while eleccion < 1 or eleccion > 4:
        print("\n¿Qué quieres hacer?")
        print("1.- Extraer datos de un año en específico")
        print("2.- Extraer datos de un rango de años")
        print("3.- Extraer datos de todos los años")
        print("4.- Salir")

        eleccion = getInputInt("Ingrese su respuesta (1 - 4): ")

    ##### Lógica #####
    limInf = 0
    limSup = 0
    years = []

    if eleccion == 1:
        limInf = getInputInt("Ingrese un año: ")
        limSup = limInf
    elif eleccion == 2:
        limInf = getInputInt("Ingrese desde donde recolectar: ")
        limSup = getInputInt("Ingrese hasta donde recolectar: ")

        limSupAux = limSup
        limSup = max(limSup, limInf)
        limInf = min(limInf, limSupAux)
    elif eleccion == 3:
        years = getAllYears(urlMain)
    elif eleccion == 4:
        exit(1)

    print()

    if not years:
        years = list(range(limInf, limSup + 1))

    results = recolectarDatos(years, urlMain)

    ##### EXPORTANDO LOS DATOS A UN EXCEL #####
    df = pd.DataFrame(results)
    df.to_excel("f1_results.xlsx", index=False)

    print("\nDatos guardados en f1_results.xlsx")
