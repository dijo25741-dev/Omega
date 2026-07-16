import logging

logger = logging.getLogger(__name__)

class CNIPlaybookEngine:
    @staticmethod
    def get_playbook(threat_stage: str, device_id: str, risk_score: float) -> dict:
        """
        Generates automated incident playbooks and mitigation strategies for CNI Operators.
        """
        # Baseline playbooks mapping
        if threat_stage == "Normal" and risk_score < 40.0:
            return {
                "active": False,
                "title": "Continuous Status Monitoring",
                "severity": "LOW",
                "steps": [
                    "Maintain active telemetry collection loop.",
                    "Verify NetworkX topological node communication latencies."
                ]
            }

        playbooks = {
            "Reconnaissance": {
                "title": "Network Reconnaissance Mitigation Plan",
                "severity": "MEDIUM",
                "steps": [
                    "Configure Boundary Firewall rule to drop port scanning packet streams.",
                    "Implement packet-rate throttling on open SSH/HMI TCP connections.",
                    "Log source IP address of scanning host to SIEM databases."
                ]
            },
            "Credential Theft": {
                "title": "Active Brute-Force Access Remediation",
                "severity": "MEDIUM",
                "steps": [
                    "Enforce dynamic lockout on operator sessions exceeding 3 failed logins.",
                    "Flag attacker source IP address on Firewall block list.",
                    "Require challenge-response verification for all SCADA/HMI commands."
                ]
            },
            "Privilege Escalation": {
                "title": "Privilege Escalation Containment Protocol",
                "severity": "HIGH",
                "steps": [
                    "De-authorize non-essential console operator accounts.",
                    "Terminate remote administration SSH sessions.",
                    "Initiate file integrity check on HMI server directories."
                ]
            },
            "Lateral Movement": {
                "title": "Network Segment Isolation Playbook",
                "severity": "HIGH",
                "steps": [
                    "Activate physical network segment boundary between SCADA and PLC LANs.",
                    "Reset API authorization keys and tokens on Historian Databases.",
                    "Audit connection nodes for unauthorized bridge links."
                ]
            },
            "PLC Targeting": {
                "title": "PLC Cyber Attack Emergency Containment",
                "severity": "CRITICAL",
                "steps": [
                    f"Isolate network interface card on target device '{device_id}'.",
                    "Transition sensor telemetry to secondary backup offline logging.",
                    "Restrict control commands to localized manual panels only.",
                    "Initiate auxiliary backup cooling systems to protect physical assets."
                ]
            },
            "Ransomware": {
                "title": "System-Wide Ransomware Lockout Protocol",
                "severity": "CRITICAL",
                "steps": [
                    "Disconnect Historian Database host from all external networks.",
                    "Freeze disk partition writes to prevent encryption routines.",
                    "Deploy active honeypot directories to exhaust encryption processes.",
                    "Verify offline backup volume integrity."
                ]
            }
        }

        # Fallback default
        stage_playbook = playbooks.get(threat_stage, {
            "title": "Active Anomaly Threat Playbook",
            "severity": "HIGH" if risk_score >= 50.0 else "MEDIUM",
            "steps": [
                f"Inspect parameters of target device '{device_id}'.",
                "Investigate operator logging logs for anomalous command patterns.",
                "Reinforce boundary firewall traffic rule matrices."
            ]
        })

        return {
            "active": True,
            "title": stage_playbook["title"],
            "threat_stage": threat_stage,
            "target_device": device_id,
            "risk_score": risk_score,
            "severity": stage_playbook["severity"],
            "steps": stage_playbook["steps"]
        }

# Singleton Instance
cni_playbook_engine = CNIPlaybookEngine()
