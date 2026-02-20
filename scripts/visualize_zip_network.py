#!/usr/bin/env python3
"""
Visualize ZIP Code Neighbor Network

生成 ZIP code 邻接网络的可视化图像
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from sqlalchemy import text

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from noah_converter.utils.config import load_config
from noah_converter.utils.db_connection import PostgreSQLConnection

# 设置样式
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 10

# 创建输出目录
output_dir = Path(__file__).parent.parent / "outputs" / "visualizations"
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("🗺️  ZIP Code Neighbor Network Visualization")
print("=" * 60)

# 连接数据库
print("\n🔌 Connecting to PostgreSQL...")
config = load_config()
pg_conn = PostgreSQLConnection(config.source_db)

# ============================================================
# 1. 加载数据
# ============================================================
print("\n📊 Loading data...")

# 加载 ZIP centroids
query = """
SELECT zip_code, center_lat, center_lon, area_km2, perimeter_km
FROM zip_centroids
ORDER BY zip_code
"""

with pg_conn.engine.connect() as conn:
    df_zips = pd.read_sql(text(query), conn)

print(f"   ✓ Loaded {len(df_zips)} ZIP codes")

# 加载 ZIP neighbors
query = """
SELECT from_zip, to_zip, distance_km, is_adjacent, shared_boundary_km
FROM zip_neighbors
ORDER BY from_zip, to_zip
"""

with pg_conn.engine.connect() as conn:
    df_neighbors = pd.read_sql(text(query), conn)

print(f"   ✓ Loaded {len(df_neighbors)} neighbor relationships")
print(f"      - Adjacent: {df_neighbors['is_adjacent'].sum()}")
print(f"      - Nearby: {(~df_neighbors['is_adjacent']).sum()}")

# ============================================================
# 2. 距离分布
# ============================================================
print("\n📈 Creating distance distribution plots...")

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# All neighbors
axes[0].hist(df_neighbors['distance_km'], bins=20, edgecolor='black', alpha=0.7, color='steelblue')
axes[0].set_xlabel('Distance (km)', fontsize=12)
axes[0].set_ylabel('Frequency', fontsize=12)
axes[0].set_title('Distance Distribution: All Neighbors', fontsize=14, fontweight='bold')
axes[0].axvline(df_neighbors['distance_km'].mean(), color='red', linestyle='--',
                linewidth=2, label=f"Mean: {df_neighbors['distance_km'].mean():.2f} km")
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# Adjacent only (if any)
adjacent_distances = df_neighbors[df_neighbors['is_adjacent']]['distance_km']
if len(adjacent_distances) > 0:
    axes[1].hist(adjacent_distances, bins=15, edgecolor='black', alpha=0.7, color='green')
    axes[1].set_xlabel('Distance (km)', fontsize=12)
    axes[1].set_ylabel('Frequency', fontsize=12)
    axes[1].set_title('Distance Distribution: Adjacent ZIPs Only', fontsize=14, fontweight='bold')
    axes[1].axvline(adjacent_distances.mean(), color='red', linestyle='--',
                    linewidth=2, label=f"Mean: {adjacent_distances.mean():.2f} km")
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3)
else:
    axes[1].text(0.5, 0.5, 'No Adjacent ZIPs\n(Mock Data)',
                ha='center', va='center', fontsize=16, color='gray',
                transform=axes[1].transAxes)
    axes[1].set_title('Distance Distribution: Adjacent ZIPs Only', fontsize=14, fontweight='bold')

plt.tight_layout()
output_file = output_dir / "01_distance_distribution.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 3. 邻居数量分布
# ============================================================
print("\n📊 Creating neighbor count distribution...")

neighbor_counts = pd.concat([
    df_neighbors['from_zip'].value_counts(),
    df_neighbors['to_zip'].value_counts()
]).groupby(level=0).sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Histogram
axes[0].hist(neighbor_counts.values, bins=15, edgecolor='black', alpha=0.7, color='coral')
axes[0].set_xlabel('Number of Neighbors', fontsize=12)
axes[0].set_ylabel('Number of ZIPs', fontsize=12)
axes[0].set_title('Distribution of Neighbor Counts per ZIP', fontsize=14, fontweight='bold')
axes[0].axvline(neighbor_counts.mean(), color='red', linestyle='--',
                linewidth=2, label=f"Mean: {neighbor_counts.mean():.1f}")
axes[0].legend(fontsize=10)
axes[0].grid(True, alpha=0.3)

# Bar chart (top 10)
top10 = neighbor_counts.head(10)
axes[1].barh(range(len(top10)), top10.values, color='coral', edgecolor='black', alpha=0.7)
axes[1].set_yticks(range(len(top10)))
axes[1].set_yticklabels(top10.index)
axes[1].set_xlabel('Number of Neighbors', fontsize=12)
axes[1].set_ylabel('ZIP Code', fontsize=12)
axes[1].set_title('Top 10 ZIPs by Neighbor Count', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='x')
axes[1].invert_yaxis()

plt.tight_layout()
output_file = output_dir / "02_neighbor_counts.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 4. 创建网络图
# ============================================================
print("\n🕸️  Creating network graph...")

G = nx.Graph()

# 添加节点
for _, row in df_zips.iterrows():
    G.add_node(row['zip_code'],
               lat=row['center_lat'],
               lon=row['center_lon'],
               area=row['area_km2'])

# 添加边
for _, row in df_neighbors.iterrows():
    G.add_edge(row['from_zip'], row['to_zip'],
               distance=row['distance_km'],
               is_adjacent=row['is_adjacent'],
               weight=1.0 / row['distance_km'])

print(f"   ✓ Created network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"   ✓ Density: {nx.density(G):.4f}")
print(f"   ✓ Connected: {nx.is_connected(G)}")

# ============================================================
# 5. 地理布局（真实位置）
# ============================================================
print("\n🗺️  Creating geographic layout visualization...")

pos_geo = {node: (data['lon'], data['lat']) for node, data in G.nodes(data=True)}

plt.figure(figsize=(16, 12))

# 区分 adjacent 和 nearby edges
adjacent_edges = [(u, v) for u, v, d in G.edges(data=True) if d['is_adjacent']]
nearby_edges = [(u, v) for u, v, d in G.edges(data=True) if not d['is_adjacent']]

# 绘制 nearby edges (灰色虚线)
nx.draw_networkx_edges(G, pos_geo, edgelist=nearby_edges,
                       edge_color='lightgray', style='dashed', width=1, alpha=0.4)

# 绘制 adjacent edges (黑色实线)
if adjacent_edges:
    nx.draw_networkx_edges(G, pos_geo, edgelist=adjacent_edges,
                           edge_color='black', width=2, alpha=0.7)

# 绘制节点
node_sizes = [G.nodes[node]['area'] * 100 for node in G.nodes()]
nx.draw_networkx_nodes(G, pos_geo,
                       node_color='skyblue',
                       node_size=node_sizes,
                       edgecolors='navy',
                       linewidths=2,
                       alpha=0.9)

# 添加标签
nx.draw_networkx_labels(G, pos_geo, font_size=9, font_weight='bold',
                        font_color='darkblue')

plt.title('NYC ZIP Code Neighbor Network\n(Geographic Layout)',
          fontsize=18, fontweight='bold', pad=20)
plt.xlabel('Longitude', fontsize=14)
plt.ylabel('Latitude', fontsize=14)
plt.axis('on')
plt.grid(True, alpha=0.3, linestyle='--')

# 图例
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color='black', linewidth=2, label='Adjacent (touching)'),
    Line2D([0], [0], color='lightgray', linewidth=1, linestyle='dashed', label='Nearby (within 10km)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='skyblue',
           markersize=10, markeredgecolor='navy', markeredgewidth=2, label='ZIP Code (size ∝ area)')
]
plt.legend(handles=legend_elements, loc='upper right', fontsize=12, framealpha=0.9)

plt.tight_layout()
output_file = output_dir / "03_geographic_network.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 6. Spring Layout（强调网络结构）
# ============================================================
print("\n🌸 Creating spring layout visualization...")

pos_spring = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

plt.figure(figsize=(16, 12))

# 绘制边
nx.draw_networkx_edges(G, pos_spring, edgelist=nearby_edges,
                       edge_color='lightgray', style='dashed', width=0.5, alpha=0.3)
if adjacent_edges:
    nx.draw_networkx_edges(G, pos_spring, edgelist=adjacent_edges,
                           edge_color='black', width=2, alpha=0.6)

# 根据 degree 着色
degrees = dict(G.degree())
node_colors = [degrees[node] for node in G.nodes()]

nodes = nx.draw_networkx_nodes(G, pos_spring,
                               node_color=node_colors,
                               node_size=500,
                               cmap='YlOrRd',
                               edgecolors='black',
                               linewidths=2,
                               alpha=0.9)

# 添加标签
nx.draw_networkx_labels(G, pos_spring, font_size=9, font_weight='bold')

plt.title('NYC ZIP Code Neighbor Network\n(Spring Layout - Emphasizes Structure)',
          fontsize=18, fontweight='bold', pad=20)
plt.colorbar(nodes, label='Degree (Number of Neighbors)', shrink=0.8, pad=0.02)
plt.axis('off')
plt.tight_layout()

output_file = output_dir / "04_spring_layout_network.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 7. 网络分析统计
# ============================================================
print("\n📊 Creating network analysis summary...")

# 计算中心性指标
degree_centrality = nx.degree_centrality(G)
betweenness_centrality = nx.betweenness_centrality(G)
closeness_centrality = nx.closeness_centrality(G)

df_centrality = pd.DataFrame({
    'zip_code': list(degree_centrality.keys()),
    'degree': list(degree_centrality.values()),
    'betweenness': list(betweenness_centrality.values()),
    'closeness': list(closeness_centrality.values())
}).sort_values('degree', ascending=False)

# 可视化前 10
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Degree Centrality
top10_degree = df_centrality.nlargest(10, 'degree')
axes[0].barh(range(len(top10_degree)), top10_degree['degree'].values,
             color='steelblue', edgecolor='black', alpha=0.7)
axes[0].set_yticks(range(len(top10_degree)))
axes[0].set_yticklabels(top10_degree['zip_code'].values)
axes[0].set_xlabel('Degree Centrality', fontsize=12)
axes[0].set_title('Top 10 by Degree\n(Most Connected)', fontsize=13, fontweight='bold')
axes[0].invert_yaxis()
axes[0].grid(True, alpha=0.3, axis='x')

# Betweenness Centrality
top10_between = df_centrality.nlargest(10, 'betweenness')
axes[1].barh(range(len(top10_between)), top10_between['betweenness'].values,
             color='coral', edgecolor='black', alpha=0.7)
axes[1].set_yticks(range(len(top10_between)))
axes[1].set_yticklabels(top10_between['zip_code'].values)
axes[1].set_xlabel('Betweenness Centrality', fontsize=12)
axes[1].set_title('Top 10 by Betweenness\n(Bridge Positions)', fontsize=13, fontweight='bold')
axes[1].invert_yaxis()
axes[1].grid(True, alpha=0.3, axis='x')

# Closeness Centrality
top10_close = df_centrality.nlargest(10, 'closeness')
axes[2].barh(range(len(top10_close)), top10_close['closeness'].values,
             color='mediumseagreen', edgecolor='black', alpha=0.7)
axes[2].set_yticks(range(len(top10_close)))
axes[2].set_yticklabels(top10_close['zip_code'].values)
axes[2].set_xlabel('Closeness Centrality', fontsize=12)
axes[2].set_title('Top 10 by Closeness\n(Central Positions)', fontsize=13, fontweight='bold')
axes[2].invert_yaxis()
axes[2].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
output_file = output_dir / "05_centrality_analysis.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 8. 统计摘要
# ============================================================
print("\n📋 Creating statistics summary...")

fig, ax = plt.subplots(figsize=(12, 8))
ax.axis('off')

stats_text = f"""
═══════════════════════════════════════════════════════════
         ZIP CODE NEIGHBOR NETWORK - STATISTICS
═══════════════════════════════════════════════════════════

NETWORK OVERVIEW
────────────────────────────────────────────────────────────
  • Total ZIP Codes:                {G.number_of_nodes()}
  • Total Neighbor Relationships:   {G.number_of_edges()}
  • Network Density:                 {nx.density(G):.4f}
  • Connected Components:            {nx.number_connected_components(G)}
  • Is Fully Connected:              {'Yes' if nx.is_connected(G) else 'No'}

DISTANCE STATISTICS
────────────────────────────────────────────────────────────
  • Average Distance:                {df_neighbors['distance_km'].mean():.2f} km
  • Median Distance:                 {df_neighbors['distance_km'].median():.2f} km
  • Min Distance:                    {df_neighbors['distance_km'].min():.2f} km
  • Max Distance:                    {df_neighbors['distance_km'].max():.2f} km
  • Std Deviation:                   {df_neighbors['distance_km'].std():.2f} km

NEIGHBOR COUNTS
────────────────────────────────────────────────────────────
  • Average Neighbors per ZIP:      {neighbor_counts.mean():.1f}
  • Median Neighbors:                {neighbor_counts.median():.0f}
  • Min Neighbors:                   {neighbor_counts.min()}
  • Max Neighbors:                   {neighbor_counts.max()}

CENTRALITY MEASURES (Top ZIPs)
────────────────────────────────────────────────────────────
  Highest Degree Centrality:        {df_centrality.iloc[0]['zip_code']} ({df_centrality.iloc[0]['degree']:.3f})
  Highest Betweenness:               {df_centrality.nlargest(1, 'betweenness').iloc[0]['zip_code']} ({df_centrality.nlargest(1, 'betweenness').iloc[0]['betweenness']:.3f})
  Highest Closeness:                 {df_centrality.nlargest(1, 'closeness').iloc[0]['zip_code']} ({df_centrality.nlargest(1, 'closeness').iloc[0]['closeness']:.3f})

ADJACENCY
────────────────────────────────────────────────────────────
  • Adjacent (Touching):             {df_neighbors['is_adjacent'].sum()}
  • Nearby (Within 10km):            {(~df_neighbors['is_adjacent']).sum()}

═══════════════════════════════════════════════════════════
"""

ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
        fontsize=11, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

output_file = output_dir / "06_statistics_summary.png"
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"   ✓ Saved: {output_file}")
plt.close()

# ============================================================
# 完成
# ============================================================
pg_conn.close()

print("\n" + "=" * 60)
print("✅ Visualization Complete!")
print("=" * 60)
print(f"\nGenerated {6} visualization files in:")
print(f"  {output_dir}/")
print("\nFiles created:")
print("  1. 01_distance_distribution.png")
print("  2. 02_neighbor_counts.png")
print("  3. 03_geographic_network.png")
print("  4. 04_spring_layout_network.png")
print("  5. 05_centrality_analysis.png")
print("  6. 06_statistics_summary.png")
print("\n" + "=" * 60)
