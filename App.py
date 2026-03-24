import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración visual
st.set_page_config(page_title="Distribuidora M&K - Cloud", layout="centered")

# 1. Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Cargar datos maestros (Inventario y Clientes)
# Asegúrate de tener estas pestañas en tu Google Sheet
try:
    inventario = conn.read(worksheet="Inventario")
    clientes = conn.read(worksheet="Clientes")
except:
    st.error("Error: No se encontró la hoja de cálculo. Revisa la configuración de Secrets.")
    st.stop()

st.title("🚀 Sistema de Gestión M&K")

menu = st.sidebar.radio("Navegación", ["Ventas de Manuel", "Resumen de Inventario", "Cierre de Caja"])

# --- MÓDULO DE VENTAS (Móvil) ---
if menu == "Ventas de Manuel":
    st.header("🛒 Registro de Preventa")
    
    with st.form("registro_pedido"):
        cliente_sel = st.selectbox("Seleccionar Cliente", clientes['Nombre'].unique())
        producto_sel = st.selectbox("Producto", inventario['Producto'].unique())
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        metodo = st.selectbox("Método de Pago", ["Efectivo", "Crédito"])
        
        btn_enviar = st.form_submit_button("Confirmar Pedido")

    if btn_enviar:
        # Calcular total
        precio_unit = inventario.loc[inventario['Producto'] == producto_sel, 'Precio'].values[0]
        total = precio_unit * cantidad
        
        # Crear nueva fila para la hoja "Ventas"
        nueva_venta = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Cliente": cliente_sel,
            "Producto": producto_sel,
            "Cantidad": cantidad,
            "Total": total,
            "Metodo": metodo,
            "Estado": "Pendiente"
        }])
        
        # Sincronizar con Google Sheets
        ventas_actuales = conn.read(worksheet="Ventas")
        df_final = pd.concat([ventas_actuales, nueva_venta], ignore_index=True)
        conn.update(worksheet="Ventas", data=df_final)
        
        st.success(f"✅ Pedido guardado para {cliente_sel}. Total: C$ {total}")

# --- MÓDULO DE INVENTARIO ---
elif menu == "Resumen de Inventario":
    st.header("📦 Stock en Bodega")
    st.dataframe(inventario, use_container_width=True)

# --- MÓDULO DE CIERRE ---
elif menu == "Cierre de Caja":
    st.header("🏦 Liquidación del Día")
    ventas_totales = conn.read(worksheet="Ventas")
    pendientes = ventas_totales[ventas_totales['Estado'] == 'Pendiente']
    
    total_efectivo = pendientes[pendientes['Metodo'] == 'Efectivo']['Total'].sum()
    
    st.metric("Efectivo que Manuel debe entregar", f"C$ {total_efectivo:,.2f}")
    st.write("Detalle de ventas hoy:")
    st.table(pendientes[['Cliente', 'Producto', 'Total']])
