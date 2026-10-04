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

    def match_drivetrain(self, text: str) -> Optional[Dict[str, Any]]:
        """Identifica la transmisión técnica a partir del texto del anuncio o título."""
        t_clean = text.lower()
        transmisiones = self._data.get("transmisiones", {})

        # 1. Búsquedas específicas de alta prioridad
        if "rx820" in t_clean or ("grx" in t_clean and "12v" in t_clean and "2x" in t_clean):
            return transmisiones.get("shimano_grx_rx820_2x12")
        if "rx810" in t_clean or ("grx 810" in t_clean):
            return transmisiones.get("shimano_grx_rx810_2x11")
        if "rx600" in t_clean or ("grx 600" in t_clean):
            return transmisiones.get("shimano_grx_rx600_2x11")
        if "rx400" in t_clean or "grx 400" in t_clean or ("grx" in t_clean and "10" in t_clean):
            return transmisiones.get("shimano_grx_rx400_2x10")
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

        # 2. Heurística general
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

        if any(w in t_clean for w in ["grx", "rx400", "rx600", "rx810", "rx820"]) and not any(m in t_clean for m in ["mecanico", "cable"]):
            return frenos.get("shimano_grx_hidraulico", {"tipo": "hidraulico", "puntos": 25.0})
        if any(w in t_clean for w in ["apex axs", "rival axs", "force axs"]):
            return frenos.get("sram_hidraulico_dot", {"tipo": "hidraulico", "puntos": 24.0})
        if "hidraulico" in t_clean or "hydraulic" in t_clean:
            return {"tipo": "hidraulico", "puntos": 24.0, "fiabilidad": 9.0, "potencia": 9.0}
        if "hy/rd" in t_clean or "hyrd" in t_clean or "semi-hidraulico" in t_clean or "semihidraulico" in t_clean:
            return frenos.get("trp_hyrd_semihidraulico", {"tipo": "semihidraulico", "puntos": 16.0})
        if "mira" in t_clean or "md-c550" in t_clean or "spyre" in t_clean or "doble piston" in t_clean:
            return frenos.get("tektro_mira_mecanico", {"tipo": "mecanico_doble", "puntos": 11.0})
        
        # Mecánico básico
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
