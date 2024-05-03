from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.edge.service import Service
import pandas as pd
import time
import re

start_time = time.time()

options = webdriver.EdgeOptions()

options.add_argument("--start-maximized")  #esto sirve maximizar el tamaño de la pantalla del webdriver.
#options.add_argument("--headless") # esto sirve para correr en segundo plano sin que se abra ventana.
driver = webdriver.Edge(options=options)


#  Función para desplazar lentamente la página hacia abajo
# Función para desplazarse gradualmente hacia abajo sin cambiar la URL
def scroll_within_same_url():
    current_url = driver.current_url  # Obtener la URL actual
    last_height = driver.execute_script("return document.documentElement.scrollHeight")

    SCROLL_INCREMENT = 1500  # Incremento de desplazamiento
    current_height = 0  # Altura actual del desplazamiento

    while True:
        # Verificar que la URL no haya cambiado
        if driver.current_url != current_url:
            break

        # Scroll vertical incremental
        driver.execute_script(f"window.scrollTo(0, {current_height}-100);")
        time.sleep(0.5)  # Pausa entre desplazamientos

        # Incrementar la altura actual
        current_height += SCROLL_INCREMENT

        # Obtener la nueva altura después del desplazamiento
        new_height = driver.execute_script("return document.documentElement.scrollHeight")

        # Si la altura actual es mayor o igual que la nueva altura, salir del bucle
        if current_height >= new_height:
            break


start_time = time.time()



# Esperar a que la página cargue completamente
time.sleep(30)

# Definir fecha actual
fecha_actual = date.today().strftime('%d-%m-%Y')

# Máximo de páginas a recorrer
max_paginas = 50

secciones = ["artesanales",
             "botas",
             "borcegos",
             "bucaneras",
             "texanas",
             "zapatillas",
             "pretemporada",
             "hombre",
             "accesorios"
             ]

excel_filename = f"sarkany_scrap_{fecha_actual}.xlsx"

# Inicializar una lista para almacenar los DataFrames
dfs = []

with (pd.ExcelWriter(excel_filename, engine='openpyxl') as writer):
    for seccion in secciones:
        categoria = seccion

        productos_recopilados = set()  # Lista para rastrear productos recopilados

        for i in range(1, max_paginas):
            try:
                # construir URL
                web_sarkany = f"https://www.rickysarkany.com/rickysarkany-aw24-{seccion}?page={i}"
                driver.get(web_sarkany)
                time.sleep(3)

                # Llamar a la función para desplazarse dentro de la misma URL
                scroll_within_same_url()

            except NoSuchElementException:
                print(f"La página no existe.")
                break


            try:
                contenedor = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    "//div[@id = 'gallery-layout-container']"))
                )
            except TimeoutException:
                print(f"No se encontraron productos de {seccion}. Saltando a la siguiente sección.")
                break  # Salir del bucle interno si no se encuentra el contenedor en la página actual

            articulos = contenedor.find_elements(By.XPATH,
                                                 ".//article[contains(@class, 'vtex-product-summary-2-x-element--mainShelf')]")

            # Inicializar las listas donde se van a cargar los datos
            lista_productos = []
            lista_precios = []
    #        lista_precios_tachados = []
            lista_link = []

            for articulo in articulos:
                try:
                    nombre_producto = articulo.find_element(By.XPATH,
                                                            ".//h3[contains(@class, 'vtex-product-summary-2-x-productNameContainer')]/span").text

                    link = articulo.find_element(By.XPATH, ".//a[contains(@class,'vtex-product-summary-2-x-clearLink')]").get_attribute("href")

                    contenedor_precio_producto = articulo.find_element(By.XPATH,
                                                                       ".//span[contains(@class, '1-x-currencyContainer')]/span").text

      #              try:
      #                  contenedor_precio_tachado = articulo.find_element(By.XPATH,
                                                                        #  ".//span[contains(@class, 'ListPrice')]/span").text

      #              except NoSuchElementException:
      #                  contenedor_precio_tachado = float('nan')

                    lista_productos.append(nombre_producto)
                    lista_precios.append(contenedor_precio_producto)
      #              lista_precios_tachados.append(contenedor_precio_tachado)
                    lista_link.append(link)
                    
                except StaleElementReferenceException:
                    print("El elemento se volvió 'stale'. Volviendo a buscarlo.")
                    driver.refresh()  # Refrescar la página
                    time.sleep(5)

                except NoSuchElementException as e:
                    print(f"No se encontró el elemento: {e}")
                
                except TimeoutException:
                    element = 'no se encontró el elemento'
                    print(element)

            # Comparar nuevos productos con productos recopilados
            productos_nuevos = [producto for producto in lista_productos if
                                producto not in productos_recopilados]

            # Agregar los productos nuevos a la lista de productos recopilados
            productos_recopilados.update(productos_nuevos)

            # Si no hay productos nuevos, detener la paginación
            if not productos_nuevos:
                break

            print(lista_productos)
            print(len(lista_productos))
            print(lista_precios)
            print(len(lista_precios))

            # Crear un DataFrame con los datos
            data = {'Fecha_relevamiento': fecha_actual,
                    "Cod_informante": "MM1",
                    "Informante": "Sarkany",
                    "Categoría": categoria,
                    'Producto': lista_productos,
                    'Link': lista_link,
                    'Precio': lista_precios,
                    'Precio_tachado': lista_precios_tachados,
                    }

            df = pd.DataFrame(data)

            # Quedarse con la parte después del símbolo "$" y eliminar los puntos y comas
            df['Precio'] = df['Precio'].astype(str).str.replace('$', '', regex=False).str.replace('.', '',
                                                                                                  regex=False).str.replace(
                ',', '.', regex=False)

            # Quedarse con la parte después del símbolo "$" y eliminar los puntos y comas
      #      df['Precio_tachado'] = df['Precio_tachado'].astype(str).str.replace('$', '', regex=False).str.replace('.',
      #                                                                                                            '',
      #                                                                                                            regex=False).str.replace(
      #          ',', '.', regex=False)

            # Convertir la columna 'Precio' a valores numéricos
            df['Precio'] = df['Precio'].astype(float)
     #       df['Precio_tachado'] = df['Precio_tachado'].astype(float)

            df['Descuento'] = round(1 - (df['Precio'] / df['Precio_tachado']), 2)
            df['Descuento'] = df['Descuento'].apply(lambda x: "{:.2%}".format(x).replace('.', ','))

            # Eliminar duplicados
            df = df.drop_duplicates()

            # Agregar el DataFrame a la lista
            dfs.append(df)

        if dfs:  # Verificar si se ha recolectado al menos un DataFrame
            # Concatenar los DataFrames de todas las secciones
            final_df = pd.concat(dfs, ignore_index=True)
            final_df = final_df.drop_duplicates()

            if not final_df.empty:  # Verificar si hay datos para escribir en una hoja
                # Escribir el DataFrame en el archivo Excel
                final_df.to_excel(writer, sheet_name='Sarkany', index=False)
            else:
                print("No hay datos para escribir en ninguna hoja del archivo Excel.")
        else:
            print("No se encontraron productos en ninguna sección.")

driver.quit()

end_time = time.time()
elapsed_time_seconds = end_time - start_time
elapsed_minutes = int(elapsed_time_seconds // 60)
elapsed_seconds = int(elapsed_time_seconds % 60)

print(f"El tiempo de ejecución del script de Sarkany fue de: {elapsed_minutes} minutos y {elapsed_seconds} segundos")