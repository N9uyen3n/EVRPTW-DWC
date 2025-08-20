# Create a rich, complete README.md for the user's GitHub repo, based on their notebook and prior discussion.

readme = r"""# EVRPTW-DWC: Electric Vehicle Routing with Time Windows and Dynamic Wireless Charging

> **Status:** Research code accompanying an internship report and a paper submission to **COMOSA 2025** (International Conference on Computation and Optimization).  
> **Notebook:** `EVRPTW_DWC.ipynb` (end-to-end modeling + experiments).

---

## ✨ Overview

This repository implements and evaluates the **Electric Vehicle Routing Problem with Time Windows and Dynamic Wireless Charging (EVRPTW-DWC)**. The model extends the classical EVRP-TW by combining:
- **Station-based charging** (full recharge to capacity \(Q\) with fixed time \(g\cdot Q\)), and  
- **Dynamic Wireless Charging (DWC)** along equipped road segments, with coverage fraction \(\omega_{ij}\in[0,1]\) and charge rate \(w\).

We formulate a mixed-integer model with **replicated charging stations** (at most \(|I|\) visits), and adopt a **lexicographic (hierarchical) objective** prioritizing:
1) **Fleet size**, 2) **Total distance**, 3) **Operational time** (travel + service + charging).

The notebook also includes a **metaheuristic layer (MACS-DWC)** for constructive search with Nearest Neighbor initialization and ant-based local updates that respect energy and time-window feasibility, including partial charging logic and DWC-aware energy propagation.

---

## 🔬 Problem Formulation (Brief)

- Nodes: customers \(I\), replicated charging stations \(F_{\text{rep}}\), depot start \(D\), depot end \(E\).
- Arcs \(A\) connect feasible pairs \((i,j)\).  
- Vehicle capacity \(C\), battery capacity \(Q\).  
- Energy consumption \(r\) (per unit distance), wireless charge rate \(w\), station charge time \(g\cdot Q\).  
- Customer \(i\) has demand \(q_i\), service time \(s_i\), time window \([a_i,b_i]\).  
- Decision variables: \(x_{ij}\) (route), \(\tau_j\) (arrival time), \(u_j\) (remaining load), \(y_j\) (state of charge).

**Objective (hierarchical):**
\[
\min\; M_1\sum_{i\in I} x_{Di} \;+\; M_2\sum_{(i,j)\in A} d_{ij}x_{ij} \;+\; 
M_3\Big(\sum_{(i,j)\in A} t_{ij}x_{ij} + \sum_{i\in I}s_i\sum_{(j,i)\in A}x_{ji} + gQ\sum_{i\in F_{\text{rep}}}\sum_{(j,i)\in A}x_{ji} \Big).
\]

**Feasibility:** flow conservation, depot balance, time windows with big-M, capacity tracking, and **energy management** that blends consumption \((r\,d_{ij})\) with DWC gains \((w\,d_{ij}\,\omega_{ij})\), plus full recharge at visited stations.

> See the report and notebook for the complete mathematical model and algorithmic details (Construct\_Solution, Optimal\_Partial\_Charge, ACS-DIST/ACS-VEI, and global pheromone updates).

---

## 📂 Repository Structure


