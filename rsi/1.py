import pandas as pd
import requests
import time
import json
import os
from datetime import datetime

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

def analizar_rsi_en_tiempo_real(config):
    par = config['par']
    temporalidad = config['temporalidad']
    tiempo_espera = config['tiempo_espera']
    periodo_rsi = config['periodo_rsi']
    
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
        elif rsi_actual < 30:
            decision = "Sobreventa - Considerar comprar"
            accion = "Comprar"
        else:
            decision = "RSI en rango normal - Mantener posición"
            accion = "Mantener"
        
        print(f'[{fecha_hora}] RSI para {par}: {rsi_actual} - {decision}')
        
        time.sleep(tiempo_espera)  # Esperar el tiempo especificado antes de la siguiente consulta

# Cargar configuración y ejecutar análisis
configuracion = cargar_configuracion()
analizar_rsi_en_tiempo_real(configuracion)
