import matplotlib.pyplot as plt
import io
import base64
import logging
from app.ai.playbook_engine import cni_playbook_engine

logger = logging.getLogger(__name__)

class CNIExplainableAI:
    @staticmethod
    def generate_explanation(
        decision: str,  # 'ALLOWED', 'BLOCKED', 'HIGH_RISK_ALERT'
        threat_stage: str,
        risk_score: float,
        confidence: float,
        operator: str = "N/A",
        command: str = "N/A",
        device_id: str = "N/A",
        anomalies: dict = None,
        telemetry: dict = None,
        guardian_reason: str = None
    ) -> dict:
        """
        Generates structured and human-readable explanations for Omega's decisions,
        including local SHAP contributions and action playbooks.
        """
        anomalies = anomalies or {}
        telemetry = telemetry or {}
        
        reasons_list = []
        
        # 1. Evaluate threat stages
        if threat_stage != "Normal":
            reasons_list.append(f"Predicted attack stage = {threat_stage} ({confidence:.0f}% confidence)")
            
        # 2. Evaluate risk levels
        reasons_list.append(f"Infrastructure Risk Score = {risk_score:.1f}")
        
        # 3. Handle anomalies
        if anomalies:
            critical_anoms = [f"{k} deviation is high ({v} Z-score)" for k, v in anomalies.items() if v > 3.0]
            if critical_anoms:
                reasons_list.append("; ".join(critical_anoms))
            else:
                reasons_list.append("Plant telemetry parameters within acceptable Z-score thresholds")
                
        # 4. Handle command validation specifics
        if decision in ["ALLOWED", "BLOCKED"]:
            reasons_list.append(f"Operator = {operator}")
            reasons_list.append(f"Command = {command}")
            reasons_list.append(f"Target Device = {device_id}")
            if guardian_reason:
                reasons_list.append(f"Guardian Evaluation = {guardian_reason}")
                
        explanation_text = " || ".join(reasons_list)
        
        # Calculate local SHAP contributions
        shap_values = CNIExplainableAI.calculate_shap_values(telemetry, threat_stage)
        shap_chart = CNIExplainableAI.generate_shap_waterfall(shap_values)
        
        # Retrieve playbook mitigation steps
        playbook = cni_playbook_engine.get_playbook(threat_stage, device_id, risk_score)
        
        return {
            "decision": decision,
            "summary": f"System validation output: {decision}.",
            "details": reasons_list,
            "raw_text": explanation_text,
            "threat_stage": threat_stage,
            "risk_score": risk_score,
            "confidence": confidence,
            "shap_attributions": shap_values,
            "shap_chart_base64": shap_chart,
            "incident_playbook": playbook
        }

    @staticmethod
    def calculate_shap_values(telemetry: dict, predicted_stage: str) -> dict:
        """
        Calculates local feature attributions representing SHAP values for the current frame.
        """
        baselines = {
            "network_latency": 2.5,
            "failed_logins": 0,
            "packet_rate": 80.0,
            "cpu_usage": 20.0,
            "memory_usage": 30.0,
            "temp_deviation": 0.0,
            "press_deviation": 0.0,
            "flow_deviation": 0.0,
            "volt_deviation": 0.0,
            "curr_deviation": 0.0,
            "anomalous_sequence_flag": 0.0
        }
        
        # Approximate feature importances of the Random Forest model for CNI
        importances = {
            "network_latency": 0.08,
            "failed_logins": 0.12,
            "packet_rate": 0.15,
            "cpu_usage": 0.08,
            "memory_usage": 0.05,
            "temp_deviation": 0.12,
            "press_deviation": 0.12,
            "flow_deviation": 0.08,
            "volt_deviation": 0.05,
            "curr_deviation": 0.05,
            "anomalous_sequence_flag": 0.10
        }
        
        # Calculate local raw difference
        raw_vals = {}
        for feat, base in baselines.items():
            val = telemetry.get(feat, base)
            # If telemetry keys are mapped slightly differently (e.g. temperature instead of deviation)
            if feat == "temp_deviation" and "temperature" in telemetry:
                val = abs(telemetry["temperature"] - 60.0) / 5.0
            elif feat == "press_deviation" and "pressure" in telemetry:
                val = abs(telemetry["pressure"] - 4.0) / 0.4
            elif feat == "flow_deviation" and "flow" in telemetry:
                val = abs(telemetry["flow"] - 50.0) / 3.0
            elif feat == "volt_deviation" and "voltage" in telemetry:
                val = abs(telemetry["voltage"] - 220.0) / 2.0
            elif feat == "curr_deviation" and "current" in telemetry:
                val = abs(telemetry["current"] - 15.0) / 0.5
                
            if feat in ["network_latency", "packet_rate", "cpu_usage", "memory_usage"]:
                # relative ratio
                raw_vals[feat] = max(0.0, (float(val) - base) / (base + 0.1))
            else:
                # absolute difference
                raw_vals[feat] = abs(float(val) - base)
                
        # Weight by importances
        scores = {}
        for feat in baselines.keys():
            scores[feat] = raw_vals[feat] * importances[feat]
            
        total = sum(scores.values())
        if total == 0 or predicted_stage == "Normal":
            # If normal, return flat zeros
            return {k: 0.0 for k in baselines.keys()}
            
        # Scale to sum to 100%
        scaled_scores = {k: round((v / total) * 100.0, 1) for k, v in scores.items()}
        return scaled_scores

    @staticmethod
    def generate_shap_waterfall(shap_values: dict) -> str:
        """
        Generates a base64 encoded horizontal bar chart representing local SHAP value attributions.
        """
        try:
            # Filter out zero values
            active_shap = {k: v for k, v in shap_values.items() if v > 0.0}
            if not active_shap:
                return ""
                
            plt.figure(figsize=(6, 3.5), facecolor='#0F172A')
            ax = plt.gca()
            ax.set_facecolor('#0F172A')
            
            labels = [k.replace("_", " ").title() for k in active_shap.keys()]
            values = list(active_shap.values())
            
            # Sort
            sorted_idx = sorted(range(len(values)), key=lambda k: values[k])
            labels = [labels[i] for i in sorted_idx]
            values = [values[i] for i in sorted_idx]
            
            # Color waterfall (amber to red)
            colors = ['#F59E0B' if val < 20 else '#EF4444' for val in values]
            
            bars = ax.barh(labels, values, color=colors, height=0.55)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#475569')
            ax.spines['bottom'].set_color('#475569')
            ax.tick_params(colors='#E2E8F0', labelsize=8)
            ax.set_title("Local Feature Contribution (SHAP Approximation)", color='#E2E8F0', fontsize=10)
            
            for bar in bars:
                width = bar.get_width()
                ax.text(
                    width + 1.0,
                    bar.get_y() + bar.get_height()/2.0,
                    f'+{width:.1f}%',
                    ha='left',
                    va='center',
                    color='#E2E8F0',
                    fontsize=8
                )
                
            plt.xlim(0, max(115.0, max(values) + 15.0 if values else 100.0))
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#0F172A')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return img_str
        except Exception as e:
            logger.error(f"Error rendering SHAP waterfall chart: {e}")
            return ""

    @staticmethod
    def generate_contribution_chart(metrics: dict) -> str:
        """
        Generates a base64 encoded matplotlib bar chart showing the relative risk contributions.
        """
        try:
            plt.figure(figsize=(6, 3), facecolor='#0F172A')
            ax = plt.gca()
            ax.set_facecolor('#0F172A')
            
            display_labels = []
            values = []
            for k, v in metrics.items():
                label = k.replace("_", " ").title()
                display_labels.append(label)
                values.append(v)
                
            # Sort factors by value
            sorted_indices = sorted(range(len(values)), key=lambda k: values[k])
            display_labels = [display_labels[i] for i in sorted_indices]
            values = [values[i] for i in sorted_indices]
            
            colors = ['#475569' if val < 10 else '#F59E0B' if val < 40 else '#EF4444' for val in values]
            
            bars = ax.barh(display_labels, values, color=colors, height=0.6)
            
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#475569')
            ax.spines['bottom'].set_color('#475569')
            ax.tick_params(colors='#E2E8F0', labelsize=8)
            ax.set_title("Risk Factor Contribution Breakdown", color='#E2E8F0', fontsize=10)
            
            for bar in bars:
                width = bar.get_width()
                if width > 0:
                    ax.text(
                        width + 1.0,
                        bar.get_y() + bar.get_height()/2.0,
                        f'{width:.1f}',
                        ha='left',
                        va='center',
                        color='#E2E8F0',
                        fontsize=8
                    )
                    
            plt.xlim(0, max(100.0, max(values) + 15.0 if values else 100.0))
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#0F172A')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return img_str
        except Exception as e:
            logger.error(f"Error creating contribution chart: {e}")
            return ""

# Singleton Instance
cni_explainable_ai = CNIExplainableAI()
