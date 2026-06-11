---
paths:
  - "src/ingest/nodes/*.py"
---

# LangGraph node conventions

Every node is a pure function:

```python
def node_name(state: IngestState) -> dict:
    ...
    return {"field_a": value, "field_b": value}
```

The graph merges the returned dict into the next state — do NOT mutate `state` in place.

**Allowed imports:** `..state`, `..schemas`, `..tools.*`
**Forbidden:** importing from other nodes. Node orchestration is `graph.py`'s job.

The routing functions (`_route_by_type`, `_route_by_confidence`) live in `graph.py` and are
the only place that reads state to decide which node runs next.
