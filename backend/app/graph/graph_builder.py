import networkx as nx
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import io
import base64
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class CNIGraphManager:
    def __init__(self):
        self.G = nx.Graph()
        self._initialize_graph()
        
    def _initialize_graph(self):
        # Add default nodes from config
        for node in settings.CNI_NODES:
            self.G.add_node(
                node["id"],
                type=node["type"],
                label=node["label"],
                status="HEALTHY",
                ip=f"192.168.10.{10 + hash(node['id']) % 240}",
                trust_score=100.0
            )
        
        # Add default edges from config
        for u, v in settings.CNI_EDGES:
            self.G.add_edge(u, v, latency_ms=1.5, bandwidth_mbps=1000)

    def add_node(self, node_id: str, node_type: str, label: str, ip: str = None):
        if not ip:
            ip = f"192.168.10.{10 + hash(node_id) % 240}"
        self.G.add_node(
            node_id,
            type=node_type,
            label=label,
            status="HEALTHY",
            ip=ip,
            trust_score=100.0
        )
        logger.info(f"Dynamically added node: {node_id} ({node_type})")

    def add_edge(self, source: str, target: str, latency_ms: float = 1.0):
        if source in self.G and target in self.G:
            self.G.add_edge(source, target, latency_ms=latency_ms, bandwidth_mbps=1000)
            logger.info(f"Dynamically added edge: {source} <-> {target}")
        else:
            logger.error(f"Cannot add edge: one or both nodes ({source}, {target}) do not exist.")

    def update_node_status(self, node_id: str, status: str, trust_score: float = None):
        if node_id in self.G:
            self.G.nodes[node_id]["status"] = status
            if trust_score is not None:
                self.G.nodes[node_id]["trust_score"] = float(trust_score)

    def get_graph_dict(self):
        # Format graph data for React D3 or Cytoscape frontend
        nodes = []
        for n, data in self.G.nodes(data=True):
            nodes.append({
                "id": n,
                "type": data.get("type", "Unknown"),
                "label": data.get("label", n),
                "status": data.get("status", "HEALTHY"),
                "ip": data.get("ip", ""),
                "trust_score": round(data.get("trust_score", 100.0), 2)
            })
            
        edges = []
        for u, v, data in self.G.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "latency_ms": data.get("latency_ms", 1.0),
                "bandwidth_mbps": data.get("bandwidth_mbps", 1000)
            })
            
        return {"nodes": nodes, "edges": edges}

    def generate_plotly_figure(self):
        # Get positions of nodes
        pos = nx.spring_layout(self.G, seed=42)
        
        edge_x = []
        edge_y = []
        for edge in self.G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        # Color mapping depending on status
        color_map = {
            "HEALTHY": "#10B981",    # Emerald green
            "ANOMALOUS": "#F59E0B",  # Amber orange
            "ATTACKED": "#EF4444"    # Red
        }

        for node in self.G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            data = self.G.nodes[node]
            
            # Hover text
            hover_info = (
                f"<b>ID:</b> {node}<br>"
                f"Type: {data.get('type')}<br>"
                f"IP: {data.get('ip')}<br>"
                f"Status: {data.get('status')}<br>"
                f"Trust Score: {data.get('trust_score'):.1f}%"
            )
            node_text.append(hover_info)
            node_color.append(color_map.get(data.get("status", "HEALTHY"), "#10B981"))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=[self.G.nodes[node].get("type") for node in self.G.nodes()],
            textposition="bottom center",
            marker=dict(
                showscale=False,
                color=node_color,
                size=35,
                line=dict(width=2, color='#fff')
            )
        )
        
        node_trace.hovertext = node_text

        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text='Omega CNI Active Topology Graph',
                    font=dict(size=16, color='#E2E8F0')
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                paper_bgcolor='#0F172A',  # Sleek dark mode slate-900
                plot_bgcolor='#0F172A'
            )
        )
        return fig

    def generate_static_plot_base64(self) -> str:
        # Create matplotlib figure for backend reporting / export
        plt.figure(figsize=(8, 6), facecolor='#0F172A')
        ax = plt.gca()
        ax.set_facecolor('#0F172A')
        
        pos = nx.spring_layout(self.G, seed=42)
        
        # Determine node colors
        color_map = {
            "HEALTHY": "#10B981",
            "ANOMALOUS": "#F59E0B",
            "ATTACKED": "#EF4444"
        }
        node_colors = [color_map.get(self.G.nodes[node].get("status", "HEALTHY"), "#10B981") for node in self.G.nodes()]
        
        nx.draw_networkx_edges(self.G, pos, edge_color='#475569', width=1.5, ax=ax)
        nx.draw_networkx_nodes(
            self.G, pos,
            node_color=node_colors,
            node_size=800,
            edgecolors='#ffffff',
            linewidths=1.5,
            ax=ax
        )
        
        # Labels
        labels = {node: f"{node}\n({self.G.nodes[node].get('type')})" for node in self.G.nodes()}
        nx.draw_networkx_labels(
            self.G, pos,
            labels=labels,
            font_size=8,
            font_color='#E2E8F0',
            font_family='sans-serif',
            ax=ax
        )
        
        plt.axis('off')
        plt.title("Omega CNI Topology Status", color='#E2E8F0', fontsize=14)
        
        # Convert plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#0F172A')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return img_str

# Singleton Instance
cni_graph_manager = CNIGraphManager()
