import pandas as pd
import requests
import time
import json
import os
from datetime import datetime

espera = 0  # Variable global para almacenar los segundos

def cargar_configuracion():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        configuracion_default = {
            "par": "BTCUSDT",
            "temporalidad": "1m",
            "tiempo_espera": 5,
            "periodo_rsi": 14
        }
        with open(config_file, 'w') as archivo:
            json.dump(configuracion_default, archivo, indent=4)
        print(f'Archivo de configuración creado: {config_file}')
    
    with open(config_file, 'r') as archivo:
        return json.load(archivo)

def obtener_precio_binance(par, temporalidad):
    url = f'https://api.binance.com/api/v3/klines?symbol={par}&interval={temporalidad}&limit=100'
    response = requests.get(url)
    data = response.json()
    precios = [float(kline[4]) for kline in data]  # Precio de cierre
    return pd.Series(precios)

def calcular_rsi(precios, periodo=14):
    cambios = precios.diff()
    ganancias = cambios.where(cambios > 0, 0)
    perdidas = -cambios.where(cambios < 0, 0)
    media_ganancias = ganancias.rolling(window=periodo).mean()
    media_perdidas = perdidas.rolling(window=periodo).mean()
    rs = media_ganancias / media_perdidas
    rsi = 100 - (100 / (1 + rs))
    return rsi

def obtener_temporalidad(config):
    global espera  # Declarar que vamos a usar la variable global
    temporalidad = config['temporalidad']
    unidad = temporalidad[-1]  # Obtener la última letra para determinar la unidad
    valor = int(temporalidad[:-1])  # Obtener el valor numérico

    # Determinar la conversión a segundos
    if unidad == 's':
        espera = valor
    elif unidad == 'm':
        espera = valor * 60
    elif unidad == 'h':
        espera = valor * 3600
    elif unidad == 'D':
        espera = valor * 86400
    elif unidad == 'S':
        espera = valor * 604800
    elif unidad == 'M':
        espera = valor * 2592000
    else:
        raise ValueError("Unidad de temporalidad no válida")

def analizar_rsi_en_tiempo_real(config):
    par = config['par']
    temporalidad = config['temporalidad']
    tiempo_espera = config['tiempo_espera']
    periodo_rsi = config['periodo_rsi']
    
    crear_csv_si_no_existe()  # Asegurarse de que el CSV existe

    while True:
        precios = obtener_precio_binance(par, temporalidad)
        rsi = calcular_rsi(precios, periodo_rsi)
        rsi_actual = rsi.iloc[-1]
        precio_actual = precios.iloc[-1]
        fecha_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Determinar si comprar o vender
        if rsi_actual > 70:
            decision = "Sobrecompra - Considerar vender"
            accion = "Vender"
            time.sleep(espera)
        elif rsi_actual < 30:
            decision = "Sobreventa - Considerar comprar"
            accion = "Comprar"
            time.sleep(espera)
        else:
            decision = "RSI en rango normal - Mantener posición"
            accion = "Mantener"
        
        print(f'[{fecha_hora}] RSI para {par}: {rsi_actual} - {decision}')
        
        # Guardar en CSV si la acción es Vender o Comprar
        if accion in ["Vender", "Comprar"]:
            with open('registro_acciones.csv', mode='a', newline='') as archivo_csv:
                writer = pd.DataFrame([[fecha_hora, precio_actual, rsi_actual, accion]], 
                                      columns=["fecha y hora", "precio", "rsi", "accion a tomar"])
                writer.to_csv(archivo_csv, header=False, index=False)

        time.sleep(tiempo_espera)  # Esperar el tiempo especificado antes de la siguiente consulta

def crear_csv_si_no_existe():
    archivo_csv = 'registro_acciones.csv'
    if not os.path.exists(archivo_csv):
        # Crear un DataFrame vacío con los nombres de las columnas
        df = pd.DataFrame(columns=["fecha y hora", "precio", "rsi", "accion a tomar"])
        df.to_csv(archivo_csv, index=False)
        print(f'Archivo CSV creado: {archivo_csv}')

# Cargar configuración y ejecutar análisis
configuracion = cargar_configuracion()
analizar_rsi_en_tiempo_real(configuracion)
crear_csv_si_no_existe()
