"""
gravel_bot.knowledge_base - Motor de Base de Conocimiento Desacoplada de Componentes
Carga la matriz técnica versionada (components_db.json) y proporciona resolución de grupos,
frenos y estándares de cuadro con scoring ponderado en caliente.
"""

import json
import os
from typing import Dict, Any, Optional, Tuple

COMPONENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "components_db.json")

class KnowledgeBase:
    _instance = None
    _data = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.load()

    def load(self):
        if os.path.exists(COMPONENTS_FILE):
            try:
                with open(COMPONENTS_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                print(f"⚠️ Error cargando components_db.json: {e}")
                self._data = {"transmisiones": {}, "frenos": {}, "estandares_cuadro": {}}
        else:
            self._data = {"transmisiones": {}, "frenos": {}, "estandares_cuadro": {}}
    # Catálogo de especificaciones de fábrica para modelos gravel conocidos del mercado español
    KNOWN_MODEL_SPECS = {
        # Megamo
        "jakar 30": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono Disc", "pvp": 1699.0},
        "jakar 20": {"dt": "sram_apex_1_1x11", "br": "sram_hidraulico_dot", "udh": 0, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono Disc", "pvp": 1699.0},
        "west 15": {"dt": "shimano_grx_rx600_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Carbono Toray", "horquilla": "Carbono", "pvp": 2499.0},
        "west 20": {"dt": "sram_apex_1_1x11", "br": "sram_hidraulico_dot", "udh": 0, "cuadro": "Carbono Toray", "horquilla": "Carbono", "pvp": 2299.0},
        "silk": {"dt": "shimano_grx_rx820_2x12", "br": "shimano_grx_hidraulico", "udh": 1, "cuadro": "Carbono Toray High Modulus", "horquilla": "Carbono", "pvp": 3499.0},
        # Conor
        "kalima grx400": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono", "pvp": 1499.0},
        "kalima grx610": {"dt": "shimano_grx_rx820_2x12", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono", "pvp": 1699.0},
        "kalima": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono", "pvp": 1499.0},
        # Orbea
        "terra h40": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio Hidroformado OMR", "horquilla": "Carbono", "pvp": 1849.0},
        "terra h30": {"dt": "shimano_grx_rx600_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio Hidroformado OMR", "horquilla": "Carbono", "pvp": 2099.0},
        "terra m30": {"dt": "shimano_grx_rx600_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Carbono OMR", "horquilla": "Carbono", "pvp": 2999.0},
        "terra m20": {"dt": "shimano_grx_rx820_2x12", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Carbono OMR", "horquilla": "Carbono", "pvp": 3699.0},
        # MMR
        "x-grip 30": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 1, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono Monocasco", "pvp": 1499.0},
        "x-grip 10": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 1, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono Monocasco", "pvp": 1799.0},
        "x-grip 00": {"dt": "sram_apex_xplr_axs_1x12", "br": "sram_hidraulico_dot", "udh": 1, "cuadro": "Aluminio 6061 Hidroformado", "horquilla": "Carbono Monocasco", "pvp": 1999.0},
        "x-tour": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 1, "cuadro": "Carbono", "horquilla": "Carbono", "pvp": 2799.0},
        # R-Raymon
        "territ comp": {"dt": "shimano_cues_u6000_1x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1299.0},
        "territ pro": {"dt": "shimano_cues_u6000_1x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1499.0},
        # Kross
        "esker 6.0": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio Superlite", "horquilla": "Carbono", "pvp": 1799.0},
        "esker 5.0": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio Superlite", "horquilla": "Carbono", "pvp": 1499.0},
        "esker 2.0": {"dt": "microshift_sword_2x10", "br": "tektro_mira_mecanico", "udh": 0, "cuadro": "Aluminio Superlite", "horquilla": "Carbono", "pvp": 1199.0},
        # Scott
        "speedster gravel 30": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio D.Butted 6061", "horquilla": "Carbono", "pvp": 1599.0},
        "speedster gravel 20": {"dt": "shimano_grx_rx600_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio D.Butted 6061", "horquilla": "Carbono", "pvp": 1799.0},
        "speedster gravel 40": {"dt": "shimano_grx_rx400_2x10", "br": "tektro_mira_mecanico", "udh": 0, "cuadro": "Aluminio D.Butted 6061", "horquilla": "Carbono", "pvp": 1399.0},
        "addict gravel 40": {"dt": "shimano_grx_rx820_2x12", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Carbono HMF", "horquilla": "Carbono HMF", "pvp": 2799.0},
        "addict gravel 30": {"dt": "sram_apex_xplr_axs_1x12", "br": "sram_hidraulico_dot", "udh": 0, "cuadro": "Carbono HMF", "horquilla": "Carbono HMF", "pvp": 3199.0},
        # Canyon
        "grizl 6": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio", "horquilla": "Carbono", "pvp": 1499.0},
        "grizl 7": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio", "horquilla": "Carbono", "pvp": 1799.0},
        "grail 7": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio", "horquilla": "Carbono", "pvp": 1799.0},
        # Cube
        "nuroad race": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Superlite", "horquilla": "Carbono", "pvp": 1699.0},
        "nuroad ex": {"dt": "shimano_grx_rx810_2x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061 Superlite", "horquilla": "Carbono", "pvp": 1549.0},
        "nuroad pro": {"dt": "shimano_grx_rx400_2x10", "br": "tektro_mira_mecanico", "udh": 0, "cuadro": "Aluminio 6061 Superlite", "horquilla": "Carbono", "pvp": 1199.0},
        "nuroad one": {"dt": "microshift_sword_2x10", "br": "tektro_mira_mecanico", "udh": 0, "cuadro": "Aluminio 6061 Superlite", "horquilla": "Carbono", "pvp": 999.0},
        # Focus
        "atlas 6": {"dt": "sram_apex_1_1x11", "br": "sram_hidraulico_dot", "udh": 0, "cuadro": "Aluminio", "horquilla": "Carbono", "pvp": 1699.0},
        # Ghost
        "asket": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio", "horquilla": "Carbono", "pvp": 1599.0},
        # KTM
        "x-strada 30": {"dt": "sram_apex_1_1x11", "br": "tektro_mira_mecanico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1199.0},
        "x-strada 20": {"dt": "shimano_grx_rx400_2x10", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1699.0},
        # Decathlon
        "grvl af": {"dt": "shimano_grx_rx820_2x12", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio AF", "horquilla": "Carbono", "pvp": 1399.0},
        "grvl 520": {"dt": "sram_apex_1_1x11", "br": "trp_hyrd_semihidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1099.0},
        "rc 520": {"dt": "shimano_grx_rx600_2x11", "br": "trp_hyrd_semihidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 899.0},
        "grvl 120": {"dt": "shimano_cues_u6000_1x10", "br": "promax_mecanico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 699.0},
        # Ciclos Corredor
        "gr-cinco": {"dt": "shimano_cues_u6000_1x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1999.0},
        "gr cinco": {"dt": "shimano_cues_u6000_1x11", "br": "shimano_grx_hidraulico", "udh": 0, "cuadro": "Aluminio 6061", "horquilla": "Carbono", "pvp": 1999.0},
    }

    def find_known_model_spec(self, text: str) -> Optional[Dict[str, Any]]:
        """Busca si el texto corresponde a un modelo canónico conocido."""
        t_clean = text.lower()
        for m_key, spec in self.KNOWN_MODEL_SPECS.items():
            if m_key in t_clean:
                return spec
        return None

    def match_drivetrain(self, text: str) -> Optional[Dict[str, Any]]:
        """Identifica la transmisión técnica a partir del texto del anuncio o título."""
        t_clean = text.lower()
        transmisiones = self._data.get("transmisiones", {})

        # 1. Búsquedas específicas de alta prioridad en texto explícito
        if "rx820" in t_clean or ("grx" in t_clean and "12v" in t_clean and "2x" in t_clean):
            return transmisiones.get("shimano_grx_rx820_2x12")
        if "rx810" in t_clean or ("grx 810" in t_clean):
            return transmisiones.get("shimano_grx_rx810_2x11")
        if "rx600" in t_clean or ("grx 600" in t_clean):
            return transmisiones.get("shimano_grx_rx600_2x11")
        if "rx400" in t_clean or "grx 400" in t_clean or ("grx" in t_clean and "10" in t_clean):
            return transmisiones.get("shimano_grx_rx400_2x10")
        if "gr-cinco" in t_clean or "gr cinco" in t_clean or ("cues" in t_clean and ("11v" in t_clean or "11" in t_clean)):
            return transmisiones.get("shimano_cues_u6000_1x11")
        if "cues" in t_clean:
            return transmisiones.get("shimano_cues_u6000_1x10")
        if "apex" in t_clean and ("axs" in t_clean or "electronico" in t_clean or "12" in t_clean):
            return transmisiones.get("sram_apex_xplr_axs_1x12")
        if "apex" in t_clean:
            return transmisiones.get("sram_apex_1_1x11")
        if "ekar" in t_clean:
            return transmisiones.get("campagnolo_ekar_gt_1x13")
        if "sword" in t_clean:
            return transmisiones.get("microshift_sword_2x10")
        if "claris" in t_clean:
            return transmisiones.get("shimano_claris_2x8")

        # 2. Resolución por modelo canónico si el anuncio omite el grupo en el título
        model_spec = self.find_known_model_spec(text)
        if model_spec and model_spec.get("dt"):
            resolved = transmisiones.get(model_spec["dt"])
            if resolved:
                return resolved

        # 3. Heurística general
        if "2x11" in t_clean:
            return transmisiones.get("shimano_grx_rx600_2x11")
        if "2x10" in t_clean:
            return transmisiones.get("shimano_grx_rx400_2x10")
        if "1x12" in t_clean:
            return transmisiones.get("sram_apex_xplr_axs_1x12")
        if "1x11" in t_clean:
            return transmisiones.get("sram_apex_1_1x11")
        if "1x10" in t_clean:
            return transmisiones.get("shimano_cues_u6000_1x10")

        return None

    def match_brakes(self, text: str) -> Dict[str, Any]:
        """Identifica los frenos técnicos a partir del texto del anuncio."""
        t_clean = text.lower()
        frenos = self._data.get("frenos", {})

        if any(w in t_clean for w in ["grx", "rx400", "rx600", "rx810", "rx820", "u6030", "gr-cinco", "gr cinco"]) and not any(m in t_clean for m in ["mecanico", "cable"]):
            return frenos.get("shimano_grx_hidraulico", {"tipo": "hidraulico", "puntos": 25.0})
        if any(w in t_clean for w in ["apex axs", "rival axs", "force axs"]):
            return frenos.get("sram_hidraulico_dot", {"tipo": "hidraulico", "puntos": 24.0})
        if "hidraulico" in t_clean or "hydraulic" in t_clean:
            return {"tipo": "hidraulico", "puntos": 24.0, "fiabilidad": 9.0, "potencia": 9.0}
        if "hy/rd" in t_clean or "hyrd" in t_clean or "semi-hidraulico" in t_clean or "semihidraulico" in t_clean:
            return frenos.get("trp_hyrd_semihidraulico", {"tipo": "semihidraulico", "puntos": 16.0})
        if "mira" in t_clean or "md-c550" in t_clean or "spyre" in t_clean or "doble piston" in t_clean:
            return frenos.get("tektro_mira_mecanico", {"tipo": "mecanico_doble", "puntos": 11.0})

        # Resolución por modelo canónico si el título del anuncio no nombra los frenos explícitamente
        model_spec = self.find_known_model_spec(text)
        if model_spec and model_spec.get("br"):
            resolved = frenos.get(model_spec["br"])
            if resolved:
                return resolved

        # Mecánico básico fallback
        return frenos.get("promax_mecanico", {"tipo": "mecanico_mono", "puntos": 7.0})
    def score_components(self, full_text: str, terreno_asfalto_pct: int = 50) -> Dict[str, Any]:
        """Calcula puntuación desacoplada para transmisión y frenos."""
        dt = self.match_drivetrain(full_text)
        br = self.match_brakes(full_text)

        # Transmisión
        if dt:
            # Ponderación según preferencia de terreno
            p_asf = dt.get("puntos_asfalto", 8.0)
            p_tie = dt.get("puntos_tierra", 8.0)
            score_trans = round((p_asf * (terreno_asfalto_pct / 100.0) + p_tie * ((100 - terreno_asfalto_pct) / 100.0)) * 2.5, 1)
            trans_info = dt
        else:
            score_trans = 14.0 # estándar desconocido
            trans_info = {"modelo": "Genérico", "tipo": "Desconocido", "climbing_ratio": 0.95}

        # Frenos
        score_frenos = br.get("puntos", 10.0)

        return {
            "score_transmision": score_trans,
            "score_frenos": score_frenos,
            "drivetrain": trans_info,
            "brakes": br
        }
