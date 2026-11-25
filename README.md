# AD371_Loadbalancer: Segmented Reverse-Proxy Load Balancer Lab

## 1. Architecture Topology Diagram & Overview
                Host / External Client (Port 80)
                               │
                               ▼
                 ┌───────────────────────────┐
                 │  public_subnet            │
                 │  172.28.10.0/24           │
                 └─────────────┬─────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │  edge-nginx (Load Bal.)   │
                 │  Dual-homed:              │
                 │   - public_subnet         │
                 │   - private_subnet        │
                 └─────────────┬─────────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │  private_subnet (internal)│
                 │  172.28.20.0/24           │
                 └───┬───────────────────┬───┘
                     │                   │
                     ▼                   ▼
        ┌─────────────────────┐ ┌─────────────────────┐
        │ backend replica 1   │ │ backend replica 2   │
        │ FastAPI (:8000 exp) │ │ FastAPI (:8000 exp) │
        │ No host port map    │ │ No host port map    │
        └─────────────────────┘ └─────────────────────┘
*Public Tier (public_subnet, 172.28.10.0/24)*: Exposes port 80 on edge-nginx to receive external HTTP traffic.

*Load Balancer (edge-nginx)*: Dual-homed across public_subnet and private_subnet; balances requests across backend replicas via Round-Robin and exposes /healthz.

*Private Tier (private_subnet, 172.28.20.0/24, internal: true)*: Hosts scaled backend replicas (:8000 exposed internally only, never published to the host).

## 2. Setup & Execution Guide

Build and start with 2 backend replicas: 
- *docker compose up -d --build --scale backend=2*
Verify running containers and port mappings: 
- *docker compose ps*
Stop services:
- *docker compose stop*
Tear down containers and networks (add -v to remove volumes if any): 
- *docker compose down --remove-orphans*

## 3. AI Disclosure
AI Tool Used: Gemini.

Prompts Submitted:
- Initial architecture prompt requesting two subnets (public_subnet, private_subnet), a dual-homed load balancer (Nginx or HAProxy) with Round-Robin upstream balancing, and at least two backend replicas on private_subnet returning a unique ID and /healthz.
- Follow-up audit, QA verification, and summary prompts used to inspect config behavior, test failover/isolation, and refine documentation.

What Worked vs. What Needed Manual Fixing / Hardening:
- Produced correctly: Isolated public_subnet and private_subnet definitions, dual-homed nginx vs. private-only backend attachment, expose: ["8000"] instead of host ports: on backends, /healthz endpoint, and Round-Robin upstream routing via service DNS (backend:8000).
- Issues caught & patched: Running docker compose run --rm --no-deps nginx nginx -t before backend started failed DNS resolution for backend:8000 (run against a running stack via docker compose exec nginx nginx -t once dependencies are up). Also added explicit proxy timeouts and proxy_next_upstream retry rules for resilience.

## 4. QA Test Summary
[x] Round-Robin Load Distribution: Sent 10 consecutive GET http://localhost/ requests; responses alternated across backend replica hostnames/IDs.

[x] High Availability & Failover: Stopped one backend container (docker stop <backend-container>), verified remaining healthy replica served requests without 502 errors, then restarted the stopped container (docker start <backend-container>) and confirmed it rejoined the pool.

[x] Network Boundary & Isolation: Verified direct host requests to backend/unmapped ports (localhost:8000, localhost:3001) and direct TCP checks to a backend's private IP on port 8000 failed while http://localhost/ succeeded.

[x] Health Check & Browser DevTools: Verified GET http://localhost/healthz returned HTTP 200 OK, and browser DevTools Network/Console showed 200 responses, connection reuse, and zero routing/console errors.
