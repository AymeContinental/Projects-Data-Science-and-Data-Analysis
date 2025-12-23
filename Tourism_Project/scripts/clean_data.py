"""
Script de Limpieza de Datos - Recursos Turísticos del Perú
Autor: [Tu nombre]
Fecha: 2024
Fuente: MINCETUR - Ministerio de Comercio Exterior y Turismo
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

class TourismDataCleaner:
    """
    Clase para limpiar y procesar datos de recursos turísticos del Perú
    """
    
    def __init__(self, input_path, output_dir):
        """
        Inicializa el limpiador de datos
        
        Args:
            input_path (str): Ruta al archivo CSV original
            output_dir (str): Directorio donde guardar los datos limpios
        """
        self.input_path = input_path
        self.output_dir = output_dir
        self.df_original = None
        self.df_clean = None
        self.stats = {}
        
    def load_data(self):
        """Carga los datos con manejo robusto de encodings"""
        print(" Cargando datos...")
        
        encodings = ['utf-8', 'latin-1', 'ISO-8859-1', 'cp1252', 'utf-8-sig']
        delimiters = [';', ',', '|', '\t']
        
        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    self.df_original = pd.read_csv(
                        self.input_path,
                        encoding=encoding,
                        delimiter=delimiter,
                        on_bad_lines='skip',
                        engine='python',
                        quoting=3
                    )
                    
                    if self.df_original.shape[1] > 5:
                        print(f" Datos cargados exitosamente")
                        print(f"  Encoding: {encoding} | Delimitador: '{delimiter}'")
                        print(f"  Registros: {len(self.df_original):,}")
                        print(f"  Columnas: {self.df_original.shape[1]}")
                        
                        self.stats['registros_originales'] = len(self.df_original)
                        self.stats['columnas_originales'] = self.df_original.shape[1]
                        return True
                        
                except Exception as e:
                    continue
        
        print(" Error: No se pudo cargar el archivo")
        return False
    
    def clean_column_names(self):
        """Estandariza los nombres de columnas"""
        print("\n🔧 Limpiando nombres de columnas...")
        
        self.df_clean = self.df_original.copy()
        
        self.df_clean.columns = (
            self.df_clean.columns
            .str.strip()
            .str.lower()
            .str.replace(' ', '_')
            .str.replace('á', 'a')
            .str.replace('é', 'e')
            .str.replace('í', 'i')
            .str.replace('ó', 'o')
            .str.replace('ú', 'u')
            .str.replace('ñ', 'n')
        )
        
        print(f" {len(self.df_clean.columns)} columnas estandarizadas")
        
    def clean_text_columns(self):
        """Limpia valores de texto"""
        print("\n Limpiando columnas de texto...")
        
        def limpiar_texto(texto):
            if pd.isna(texto):
                return texto
            texto = str(texto).strip()
            if not texto.isupper():
                texto = texto.title()
            return texto
        
        columnas_texto = self.df_clean.select_dtypes(include=['object']).columns
        cleaned_count = 0
        
        for col in columnas_texto:
            if 'url' not in col.lower() and 'http' not in col.lower():
                try:
                    self.df_clean[col] = self.df_clean[col].apply(limpiar_texto)
                    cleaned_count += 1
                except:
                    pass
        
        print(f" {cleaned_count} columnas de texto limpiadas")
    
    def handle_missing_values(self):
        """Maneja valores nulos"""
        print("\n Manejando valores nulos...")
        
        nulos_antes = self.df_clean.isnull().sum().sum()
        
        for col in self.df_clean.columns:
            if self.df_clean[col].isnull().sum() > 0:
                if self.df_clean[col].dtype == 'object':
                    if 'url' not in col.lower() and 'fecha' not in col.lower():
                        self.df_clean[col] = self.df_clean[col].fillna('NO ESPECIFICADO')
        
        nulos_despues = self.df_clean.isnull().sum().sum()
        
        print(f" Valores nulos: {nulos_antes:,} → {nulos_despues:,}")
        self.stats['nulos_originales'] = nulos_antes
        self.stats['nulos_finales'] = nulos_despues
    
    def remove_duplicates(self):
        """Elimina registros duplicados"""
        print("\n Eliminando duplicados...")
        
        registros_antes = len(self.df_clean)
        self.df_clean = self.df_clean.drop_duplicates()
        duplicados_eliminados = registros_antes - len(self.df_clean)
        
        print(f" Duplicados eliminados: {duplicados_eliminados:,}")
        self.stats['duplicados_eliminados'] = duplicados_eliminados
    
    def add_new_columns(self):
        """Agrega columnas útiles para análisis"""
        print("\n Creando nuevas columnas...")
        
        # ID único
        self.df_clean['id_recurso'] = range(1, len(self.df_clean) + 1)
        print(" Columna 'id_recurso' creada")
        
        # Verificar coordenadas
        coord_cols = [col for col in self.df_clean.columns if 'lat' in col.lower() or 'long' in col.lower()]
        
        if len(coord_cols) >= 2:
            lat_col = [c for c in coord_cols if 'lat' in c.lower()][0]
            lon_col = [c for c in coord_cols if 'lon' in c.lower()][0]
            
            self.df_clean[lat_col] = pd.to_numeric(self.df_clean[lat_col], errors='coerce')
            self.df_clean[lon_col] = pd.to_numeric(self.df_clean[lon_col], errors='coerce')
            
            self.df_clean['tiene_coordenadas'] = (
                (~self.df_clean[lat_col].isna()) & 
                (~self.df_clean[lon_col].isna())
            )
            
            con_coords = self.df_clean['tiene_coordenadas'].sum()
            print(f" Columna 'tiene_coordenadas' creada ({con_coords:,} recursos)")
        
        self.stats['registros_finales'] = len(self.df_clean)
        self.stats['columnas_finales'] = len(self.df_clean.columns)
    
    def save_clean_data(self):
        """Guarda los datos limpios"""
        print("\n Guardando datos limpios...")
        
        # Crear directorio si no existe
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Guardar CSV
        csv_path = os.path.join(self.output_dir, 'inventario_recursos_turisticos_limpio.csv')
        self.df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f" CSV guardado: {csv_path}")
        
        # Guardar Excel
        try:
            excel_path = os.path.join(self.output_dir, 'inventario_recursos_turisticos_limpio.xlsx')
            self.df_clean.to_excel(excel_path, index=False, engine='openpyxl')
            print(f" Excel guardado: {excel_path}")
        except:
            print(" No se pudo guardar Excel (instala openpyxl)")
        
        # Guardar resumen
        self.save_summary()
    
    def save_summary(self):
        """Guarda un resumen del proceso de limpieza"""
        resumen = f"""
{'=' * 80}
RESUMEN DEL PROCESO DE LIMPIEZA DE DATOS
{'=' * 80}

Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Fuente: MINCETUR - Inventario Nacional de Recursos Turísticos

DATOS ORIGINALES:
- Registros: {self.stats.get('registros_originales', 0):,}
- Columnas: {self.stats.get('columnas_originales', 0)}
- Valores nulos: {self.stats.get('nulos_originales', 0):,}

TRANSFORMACIONES REALIZADAS:
- Nombres de columnas estandarizados
- Valores de texto limpiados y capitalizados
- Valores nulos manejados apropiadamente
- Duplicados eliminados: {self.stats.get('duplicados_eliminados', 0):,}
- Nuevas columnas agregadas

DATOS LIMPIOS:
- Registros: {self.stats.get('registros_finales', 0):,}
- Columnas: {self.stats.get('columnas_finales', 0)}
- Valores nulos: {self.stats.get('nulos_finales', 0):,}

 Datos listos para análisis en Power BI y Looker Studio
{'=' * 80}
"""
        
        summary_path = os.path.join(self.output_dir, 'resumen_limpieza.txt')
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(resumen)
        
        print(f" Resumen guardado: {summary_path}")
        print(resumen)
    
    def run(self):
        """Ejecuta todo el proceso de limpieza"""
        print("=" * 80)
        print("INICIO DEL PROCESO DE LIMPIEZA DE DATOS")
        print("=" * 80)
        
        if not self.load_data():
            return False
        
        self.clean_column_names()
        self.clean_text_columns()
        self.handle_missing_values()
        self.remove_duplicates()
        self.add_new_columns()
        self.save_clean_data()
        
        print("\n" + "=" * 80)
        print(" PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        
        return True


def main():
    """Función principal"""
    # Rutas de archivos
    INPUT_FILE = 'data/raw/inventario_recursos_turisticos.csv'
    OUTPUT_DIR = 'data/cleaned'
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(INPUT_FILE):
        print(f" Error: No se encuentra el archivo {INPUT_FILE}")
        sys.exit(1)
    
    # Crear instancia del limpiador
    cleaner = TourismDataCleaner(INPUT_FILE, OUTPUT_DIR)
    
    # Ejecutar limpieza
    success = cleaner.run()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()