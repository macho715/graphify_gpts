# Graphify Backend Acceptance Test Report — 5 Rounds

- Rounds: 5
- Checks per round: 7
- Total checks: 35
- PASS checks: 35
- FAIL checks: 0
- Result: PASS

## Round 1

# Graphify Backend 5x Test Report

- Base URL: `http://127.0.0.1:8765`
- Fixture: `/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo`

| No | Test | Status |
|---:|---|---|
| 1 | 1_health | PASS |
| 2 | 2_build_local_fixture | PASS |
| 3 | 3_stats_persistent_graph | PASS |
| 4 | 4_query_returns_hits | PASS |
| 5 | 5_path_explain_affected | PASS |
| 6 | 6_export_artifact_download | PASS |
| 7 | 7_update_existing_graph_id | PASS |

## Raw Results
```json
[
  {
    "test": "1_health",
    "status": "PASS",
    "payload": {
      "status": "ok",
      "auth_mode": "none",
      "data_dir": "/mnt/data/graphify_full_stack_ready/backend/data_test",
      "allowed_hosts": [
        "github.com",
        "codeload.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com"
      ],
      "run_mode": "worker"
    }
  },
  {
    "test": "2_build_local_fixture",
    "status": "PASS",
    "payload": {
      "job_id": "a576d5324c5446c6",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r1",
      "message": "completed"
    }
  },
  {
    "test": "3_stats_persistent_graph",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r1",
      "nodes": 20,
      "edges": 24,
      "files": 5,
      "symbols": 11,
      "skipped_files": 0,
      "generated_at": "2026-06-17T13:53:41.282238+00:00",
      "source": {
        "type": "local_path",
        "url": null,
        "branch": null,
        "path": "/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo"
      }
    }
  },
  {
    "test": "4_query_returns_hits",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r1",
      "query": "invoice validate shipment",
      "hits": [
        {
          "node_id": "symbol:src/invoice.py:InvoiceValidator",
          "label": "InvoiceValidator",
          "type": "class",
          "score": 1.8708,
          "evidence": "class InvoiceValidator line 4",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:README.md",
          "label": "README.md",
          "type": "file",
          "score": 1.8371,
          "evidence": "# Tiny Invoice Repo\nThis fixture validates invoice shipment cost logic and Graphify query/path/explain operations.\n## Workflow\n1. Load invoice rows.\n2. Validate shipment amount.",
          "path": "README.md"
        },
        {
          "node_id": "file:src/invoice.py",
          "label": "invoice.py",
          "type": "file",
          "score": 1.4924,
          "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
          "path": "src/invoice.py"
        },
        {
          "node_id": "symbol:src/invoice.py:validate_invoice",
          "label": "validate_invoice",
          "type": "function",
          "score": 1.2649,
          "evidence": "def validate_invoice(...) line 10",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:docs/process.md",
          "label": "process.md",
          "type": "file",
          "score": 1.2511,
          "evidence": "# Shipment Validation Process\n## Invoice Evidence\nCI/PL, BL, BOE, DO and delivery note must match the invoice claim.\n## Affected Analysis",
          "path": "docs/process.md"
        }
      ]
    }
  },
  {
    "test": "5_path_explain_affected",
    "status": "PASS",
    "payload": {
      "path": {
        "graph_id": "smoke-tiny-r1",
        "found": true,
        "path": [
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/a576d5324c5446c6/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a576d5324c5446c6",
              "src"
            ]
          },
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "symbol:src/invoice.py:validate_invoice",
            "type": "function",
            "label": "validate_invoice",
            "path": "src/invoice.py",
            "line": 10,
            "summary": "Python function validate_invoice",
            "evidence": "def validate_invoice(...) line 10",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "validate_invoice",
              "validate_invoice",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "validate_invoice",
              "def",
              "validate_invoice",
              "line"
            ]
          }
        ],
        "edges": [
          {
            "id": "733cfeb352a25873",
            "source": "project:root",
            "target": "file:src/invoice.py",
            "relation": "CONTAINS",
            "evidence": "src/invoice.py"
          },
          {
            "id": "0e920ac02079e8fd",
            "source": "file:src/invoice.py",
            "target": "symbol:src/invoice.py:validate_invoice",
            "relation": "DEFINES",
            "evidence": "line 15"
          }
        ]
      },
      "explain": {
        "graph_id": "smoke-tiny-r1",
        "node": {
          "id": "symbol:src/invoice.py:validate_invoice",
          "type": "function",
          "label": "validate_invoice",
          "path": "src/invoice.py",
          "line": 10,
          "summary": "Python function validate_invoice",
          "evidence": "def validate_invoice(...) line 10",
          "tokens": [
            "symbol",
            "src",
            "invoice",
            "py",
            "validate_invoice",
            "validate_invoice",
            "function",
            "src",
            "invoice",
            "py",
            "python",
            "function",
            "validate_invoice",
            "def",
            "validate_invoice",
            "line"
          ]
        },
        "neighbors": [
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "external:.shipment",
            "type": "external_import",
            "label": ".shipment",
            "summary": "Imported Python module",
            "evidence": "from .shipment import ...",
            "tokens": [
              "external",
              "shipment",
              "shipment",
              "external_import",
              "imported",
              "python",
              "module",
              "from",
              "shipment",
              "import"
            ]
          },
          {
            "id": "symbol:src/invoice.py:InvoiceValidator",
            "type": "class",
            "label": "InvoiceValidator",
            "path": "src/invoice.py",
            "line": 4,
            "summary": "Validates invoice amount and shipment lane evidence.",
            "evidence": "class InvoiceValidator line 4",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "invoicevalidator",
              "invoicevalidator",
              "class",
              "src",
              "invoice",
              "py",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "class",
              "invoicevalidator",
              "line"
            ]
          },
          {
            "id": "symbol:src/invoice.py:__init__",
            "type": "function",
            "label": "__init__",
            "path": "src/invoice.py",
            "line": 7,
            "summary": "Python function __init__",
            "evidence": "def __init__(...) line 7",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "__init__",
              "__init__",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "__init__",
              "def",
              "__init__",
              "line"
            ]
          },
          {
            "id": "file:src/shipment.py",
            "type": "file",
            "label": "shipment.py",
            "path": "src/shipment.py",
            "size_bytes": 232,
            "sha256": "a47d073fedb2627342561d40456e14d6429f01e104024bedf63ba0cf15c84bec",
            "summary": "def normalize_lane(lane: str) -> str: \"\"\"Normalize POL/POD lane string.\"\"\" return lane.strip().upper().replace(\" \", \"-\") def calculate_freight(base: float, surcharge: float) -> float:",
            "evidence": "def normalize_lane(lane: str) -> str:\n\"\"\"Normalize POL/POD lane string.\"\"\"\nreturn lane.strip().upper().replace(\" \", \"-\")\ndef calculate_freight(base: float, surcharge: float) -> float:\nreturn round(base + surcharge, 2)",
            "tokens": [
              "file",
              "src",
              "shipment",
              "py",
              "shipment",
              "py",
              "file",
              "src",
              "shipment",
              "py",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "return",
              "round",
              "base",
              "surcharge"
            ]
          },
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/a576d5324c5446c6/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a576d5324c5446c6",
              "src"
            ]
          },
          {
            "id": "dir:src",
            "type": "directory",
            "label": "src",
            "path": "src",
            "summary": "Directory",
            "tokens": [
              "dir",
              "src",
              "src",
              "directory",
              "src",
              "directory"
            ]
          }
        ],
        "evidence": [
          "def validate_invoice(...) line 10",
          "line 15",
          "line 10",
          "line 1",
          "line 4",
          "line 15",
          "line 7",
          "line 10",
          ".shipment",
          "src/invoice.py",
          "src/invoice.py"
        ],
        "summary": "validate_invoice is a function with 7 neighbor nodes within depth 2."
      },
      "affected_count": 13
    }
  },
  {
    "test": "6_export_artifact_download",
    "status": "PASS",
    "payload": {
      "export": {
        "graph_id": "smoke-tiny-r1",
        "format": "zip",
        "artifact_token": "eyJleHAiOjE3ODE3MDUzMjEsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMSIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMS9ncmFwaGlmeS1vdXQuemlwIn0.lL_ZKnqo06V2QFWEUkRz9uPVvH-_WGis_WTdDa2dTYM",
        "artifact_url": "/v1/graphify/artifacts/eyJleHAiOjE3ODE3MDUzMjEsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMSIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMS9ncmFwaGlmeS1vdXQuemlwIn0.lL_ZKnqo06V2QFWEUkRz9uPVvH-_WGis_WTdDa2dTYM",
        "expires_in_seconds": 900
      },
      "bytes": 8389
    }
  },
  {
    "test": "7_update_existing_graph_id",
    "status": "PASS",
    "payload": {
      "job_id": "cc944469b3fe4fd7",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r1",
      "message": "completed"
    }
  }
]
```

## Round 2

# Graphify Backend 5x Test Report

- Base URL: `http://127.0.0.1:8765`
- Fixture: `/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo`

| No | Test | Status |
|---:|---|---|
| 1 | 1_health | PASS |
| 2 | 2_build_local_fixture | PASS |
| 3 | 3_stats_persistent_graph | PASS |
| 4 | 4_query_returns_hits | PASS |
| 5 | 5_path_explain_affected | PASS |
| 6 | 6_export_artifact_download | PASS |
| 7 | 7_update_existing_graph_id | PASS |

## Raw Results
```json
[
  {
    "test": "1_health",
    "status": "PASS",
    "payload": {
      "status": "ok",
      "auth_mode": "none",
      "data_dir": "/mnt/data/graphify_full_stack_ready/backend/data_test",
      "allowed_hosts": [
        "github.com",
        "codeload.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com"
      ],
      "run_mode": "worker"
    }
  },
  {
    "test": "2_build_local_fixture",
    "status": "PASS",
    "payload": {
      "job_id": "9eac093f546e475d",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r2",
      "message": "completed"
    }
  },
  {
    "test": "3_stats_persistent_graph",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r2",
      "nodes": 20,
      "edges": 24,
      "files": 5,
      "symbols": 11,
      "skipped_files": 0,
      "generated_at": "2026-06-17T13:53:42.931957+00:00",
      "source": {
        "type": "local_path",
        "url": null,
        "branch": null,
        "path": "/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo"
      }
    }
  },
  {
    "test": "4_query_returns_hits",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r2",
      "query": "invoice validate shipment",
      "hits": [
        {
          "node_id": "symbol:src/invoice.py:InvoiceValidator",
          "label": "InvoiceValidator",
          "type": "class",
          "score": 1.8708,
          "evidence": "class InvoiceValidator line 4",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:README.md",
          "label": "README.md",
          "type": "file",
          "score": 1.8371,
          "evidence": "# Tiny Invoice Repo\nThis fixture validates invoice shipment cost logic and Graphify query/path/explain operations.\n## Workflow\n1. Load invoice rows.\n2. Validate shipment amount.",
          "path": "README.md"
        },
        {
          "node_id": "file:src/invoice.py",
          "label": "invoice.py",
          "type": "file",
          "score": 1.4924,
          "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
          "path": "src/invoice.py"
        },
        {
          "node_id": "symbol:src/invoice.py:validate_invoice",
          "label": "validate_invoice",
          "type": "function",
          "score": 1.2649,
          "evidence": "def validate_invoice(...) line 10",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:docs/process.md",
          "label": "process.md",
          "type": "file",
          "score": 1.2511,
          "evidence": "# Shipment Validation Process\n## Invoice Evidence\nCI/PL, BL, BOE, DO and delivery note must match the invoice claim.\n## Affected Analysis",
          "path": "docs/process.md"
        }
      ]
    }
  },
  {
    "test": "5_path_explain_affected",
    "status": "PASS",
    "payload": {
      "path": {
        "graph_id": "smoke-tiny-r2",
        "found": true,
        "path": [
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/9eac093f546e475d/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "eac093f546e475d",
              "src"
            ]
          },
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "symbol:src/invoice.py:validate_invoice",
            "type": "function",
            "label": "validate_invoice",
            "path": "src/invoice.py",
            "line": 10,
            "summary": "Python function validate_invoice",
            "evidence": "def validate_invoice(...) line 10",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "validate_invoice",
              "validate_invoice",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "validate_invoice",
              "def",
              "validate_invoice",
              "line"
            ]
          }
        ],
        "edges": [
          {
            "id": "733cfeb352a25873",
            "source": "project:root",
            "target": "file:src/invoice.py",
            "relation": "CONTAINS",
            "evidence": "src/invoice.py"
          },
          {
            "id": "0e920ac02079e8fd",
            "source": "file:src/invoice.py",
            "target": "symbol:src/invoice.py:validate_invoice",
            "relation": "DEFINES",
            "evidence": "line 15"
          }
        ]
      },
      "explain": {
        "graph_id": "smoke-tiny-r2",
        "node": {
          "id": "symbol:src/invoice.py:validate_invoice",
          "type": "function",
          "label": "validate_invoice",
          "path": "src/invoice.py",
          "line": 10,
          "summary": "Python function validate_invoice",
          "evidence": "def validate_invoice(...) line 10",
          "tokens": [
            "symbol",
            "src",
            "invoice",
            "py",
            "validate_invoice",
            "validate_invoice",
            "function",
            "src",
            "invoice",
            "py",
            "python",
            "function",
            "validate_invoice",
            "def",
            "validate_invoice",
            "line"
          ]
        },
        "neighbors": [
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "external:.shipment",
            "type": "external_import",
            "label": ".shipment",
            "summary": "Imported Python module",
            "evidence": "from .shipment import ...",
            "tokens": [
              "external",
              "shipment",
              "shipment",
              "external_import",
              "imported",
              "python",
              "module",
              "from",
              "shipment",
              "import"
            ]
          },
          {
            "id": "symbol:src/invoice.py:InvoiceValidator",
            "type": "class",
            "label": "InvoiceValidator",
            "path": "src/invoice.py",
            "line": 4,
            "summary": "Validates invoice amount and shipment lane evidence.",
            "evidence": "class InvoiceValidator line 4",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "invoicevalidator",
              "invoicevalidator",
              "class",
              "src",
              "invoice",
              "py",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "class",
              "invoicevalidator",
              "line"
            ]
          },
          {
            "id": "symbol:src/invoice.py:__init__",
            "type": "function",
            "label": "__init__",
            "path": "src/invoice.py",
            "line": 7,
            "summary": "Python function __init__",
            "evidence": "def __init__(...) line 7",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "__init__",
              "__init__",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "__init__",
              "def",
              "__init__",
              "line"
            ]
          },
          {
            "id": "file:src/shipment.py",
            "type": "file",
            "label": "shipment.py",
            "path": "src/shipment.py",
            "size_bytes": 232,
            "sha256": "a47d073fedb2627342561d40456e14d6429f01e104024bedf63ba0cf15c84bec",
            "summary": "def normalize_lane(lane: str) -> str: \"\"\"Normalize POL/POD lane string.\"\"\" return lane.strip().upper().replace(\" \", \"-\") def calculate_freight(base: float, surcharge: float) -> float:",
            "evidence": "def normalize_lane(lane: str) -> str:\n\"\"\"Normalize POL/POD lane string.\"\"\"\nreturn lane.strip().upper().replace(\" \", \"-\")\ndef calculate_freight(base: float, surcharge: float) -> float:\nreturn round(base + surcharge, 2)",
            "tokens": [
              "file",
              "src",
              "shipment",
              "py",
              "shipment",
              "py",
              "file",
              "src",
              "shipment",
              "py",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "return",
              "round",
              "base",
              "surcharge"
            ]
          },
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/9eac093f546e475d/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "eac093f546e475d",
              "src"
            ]
          },
          {
            "id": "dir:src",
            "type": "directory",
            "label": "src",
            "path": "src",
            "summary": "Directory",
            "tokens": [
              "dir",
              "src",
              "src",
              "directory",
              "src",
              "directory"
            ]
          }
        ],
        "evidence": [
          "def validate_invoice(...) line 10",
          "line 15",
          "line 10",
          "line 1",
          "line 4",
          "line 15",
          "line 7",
          "line 10",
          ".shipment",
          "src/invoice.py",
          "src/invoice.py"
        ],
        "summary": "validate_invoice is a function with 7 neighbor nodes within depth 2."
      },
      "affected_count": 13
    }
  },
  {
    "test": "6_export_artifact_download",
    "status": "PASS",
    "payload": {
      "export": {
        "graph_id": "smoke-tiny-r2",
        "format": "zip",
        "artifact_token": "eyJleHAiOjE3ODE3MDUzMjIsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMiIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMi9ncmFwaGlmeS1vdXQuemlwIn0.JydgvD6w1ndnre9qX3RaGnFdssjWRfsq_Ex9SwOmF6Q",
        "artifact_url": "/v1/graphify/artifacts/eyJleHAiOjE3ODE3MDUzMjIsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMiIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMi9ncmFwaGlmeS1vdXQuemlwIn0.JydgvD6w1ndnre9qX3RaGnFdssjWRfsq_Ex9SwOmF6Q",
        "expires_in_seconds": 900
      },
      "bytes": 8392
    }
  },
  {
    "test": "7_update_existing_graph_id",
    "status": "PASS",
    "payload": {
      "job_id": "c233bda1fe614f2c",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r2",
      "message": "completed"
    }
  }
]
```

## Round 3

# Graphify Backend 5x Test Report

- Base URL: `http://127.0.0.1:8765`
- Fixture: `/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo`

| No | Test | Status |
|---:|---|---|
| 1 | 1_health | PASS |
| 2 | 2_build_local_fixture | PASS |
| 3 | 3_stats_persistent_graph | PASS |
| 4 | 4_query_returns_hits | PASS |
| 5 | 5_path_explain_affected | PASS |
| 6 | 6_export_artifact_download | PASS |
| 7 | 7_update_existing_graph_id | PASS |

## Raw Results
```json
[
  {
    "test": "1_health",
    "status": "PASS",
    "payload": {
      "status": "ok",
      "auth_mode": "none",
      "data_dir": "/mnt/data/graphify_full_stack_ready/backend/data_test",
      "allowed_hosts": [
        "github.com",
        "codeload.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com"
      ],
      "run_mode": "worker"
    }
  },
  {
    "test": "2_build_local_fixture",
    "status": "PASS",
    "payload": {
      "job_id": "3036ec36c22e4259",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r3",
      "message": "completed"
    }
  },
  {
    "test": "3_stats_persistent_graph",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r3",
      "nodes": 20,
      "edges": 24,
      "files": 5,
      "symbols": 11,
      "skipped_files": 0,
      "generated_at": "2026-06-17T13:53:44.408723+00:00",
      "source": {
        "type": "local_path",
        "url": null,
        "branch": null,
        "path": "/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo"
      }
    }
  },
  {
    "test": "4_query_returns_hits",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r3",
      "query": "invoice validate shipment",
      "hits": [
        {
          "node_id": "symbol:src/invoice.py:InvoiceValidator",
          "label": "InvoiceValidator",
          "type": "class",
          "score": 1.8708,
          "evidence": "class InvoiceValidator line 4",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:README.md",
          "label": "README.md",
          "type": "file",
          "score": 1.8371,
          "evidence": "# Tiny Invoice Repo\nThis fixture validates invoice shipment cost logic and Graphify query/path/explain operations.\n## Workflow\n1. Load invoice rows.\n2. Validate shipment amount.",
          "path": "README.md"
        },
        {
          "node_id": "file:src/invoice.py",
          "label": "invoice.py",
          "type": "file",
          "score": 1.4924,
          "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
          "path": "src/invoice.py"
        },
        {
          "node_id": "symbol:src/invoice.py:validate_invoice",
          "label": "validate_invoice",
          "type": "function",
          "score": 1.2649,
          "evidence": "def validate_invoice(...) line 10",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:docs/process.md",
          "label": "process.md",
          "type": "file",
          "score": 1.2511,
          "evidence": "# Shipment Validation Process\n## Invoice Evidence\nCI/PL, BL, BOE, DO and delivery note must match the invoice claim.\n## Affected Analysis",
          "path": "docs/process.md"
        }
      ]
    }
  },
  {
    "test": "5_path_explain_affected",
    "status": "PASS",
    "payload": {
      "path": {
        "graph_id": "smoke-tiny-r3",
        "found": true,
        "path": [
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/3036ec36c22e4259/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "ec36c22e4259",
              "src"
            ]
          },
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "symbol:src/invoice.py:validate_invoice",
            "type": "function",
            "label": "validate_invoice",
            "path": "src/invoice.py",
            "line": 10,
            "summary": "Python function validate_invoice",
            "evidence": "def validate_invoice(...) line 10",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "validate_invoice",
              "validate_invoice",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "validate_invoice",
              "def",
              "validate_invoice",
              "line"
            ]
          }
        ],
        "edges": [
          {
            "id": "733cfeb352a25873",
            "source": "project:root",
            "target": "file:src/invoice.py",
            "relation": "CONTAINS",
            "evidence": "src/invoice.py"
          },
          {
            "id": "0e920ac02079e8fd",
            "source": "file:src/invoice.py",
            "target": "symbol:src/invoice.py:validate_invoice",
            "relation": "DEFINES",
            "evidence": "line 15"
          }
        ]
      },
      "explain": {
        "graph_id": "smoke-tiny-r3",
        "node": {
          "id": "symbol:src/invoice.py:validate_invoice",
          "type": "function",
          "label": "validate_invoice",
          "path": "src/invoice.py",
          "line": 10,
          "summary": "Python function validate_invoice",
          "evidence": "def validate_invoice(...) line 10",
          "tokens": [
            "symbol",
            "src",
            "invoice",
            "py",
            "validate_invoice",
            "validate_invoice",
            "function",
            "src",
            "invoice",
            "py",
            "python",
            "function",
            "validate_invoice",
            "def",
            "validate_invoice",
            "line"
          ]
        },
        "neighbors": [
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "external:.shipment",
            "type": "external_import",
            "label": ".shipment",
            "summary": "Imported Python module",
            "evidence": "from .shipment import ...",
            "tokens": [
              "external",
              "shipment",
              "shipment",
              "external_import",
              "imported",
              "python",
              "module",
              "from",
              "shipment",
              "import"
            ]
          },
          {
            "id": "symbol:src/invoice.py:InvoiceValidator",
            "type": "class",
            "label": "InvoiceValidator",
            "path": "src/invoice.py",
            "line": 4,
            "summary": "Validates invoice amount and shipment lane evidence.",
            "evidence": "class InvoiceValidator line 4",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "invoicevalidator",
              "invoicevalidator",
              "class",
              "src",
              "invoice",
              "py",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "class",
              "invoicevalidator",
              "line"
            ]
          },
          {
            "id": "symbol:src/invoice.py:__init__",
            "type": "function",
            "label": "__init__",
            "path": "src/invoice.py",
            "line": 7,
            "summary": "Python function __init__",
            "evidence": "def __init__(...) line 7",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "__init__",
              "__init__",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "__init__",
              "def",
              "__init__",
              "line"
            ]
          },
          {
            "id": "file:src/shipment.py",
            "type": "file",
            "label": "shipment.py",
            "path": "src/shipment.py",
            "size_bytes": 232,
            "sha256": "a47d073fedb2627342561d40456e14d6429f01e104024bedf63ba0cf15c84bec",
            "summary": "def normalize_lane(lane: str) -> str: \"\"\"Normalize POL/POD lane string.\"\"\" return lane.strip().upper().replace(\" \", \"-\") def calculate_freight(base: float, surcharge: float) -> float:",
            "evidence": "def normalize_lane(lane: str) -> str:\n\"\"\"Normalize POL/POD lane string.\"\"\"\nreturn lane.strip().upper().replace(\" \", \"-\")\ndef calculate_freight(base: float, surcharge: float) -> float:\nreturn round(base + surcharge, 2)",
            "tokens": [
              "file",
              "src",
              "shipment",
              "py",
              "shipment",
              "py",
              "file",
              "src",
              "shipment",
              "py",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "return",
              "round",
              "base",
              "surcharge"
            ]
          },
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/3036ec36c22e4259/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "ec36c22e4259",
              "src"
            ]
          },
          {
            "id": "dir:src",
            "type": "directory",
            "label": "src",
            "path": "src",
            "summary": "Directory",
            "tokens": [
              "dir",
              "src",
              "src",
              "directory",
              "src",
              "directory"
            ]
          }
        ],
        "evidence": [
          "def validate_invoice(...) line 10",
          "line 15",
          "line 10",
          "line 1",
          "line 4",
          "line 15",
          "line 7",
          "line 10",
          ".shipment",
          "src/invoice.py",
          "src/invoice.py"
        ],
        "summary": "validate_invoice is a function with 7 neighbor nodes within depth 2."
      },
      "affected_count": 13
    }
  },
  {
    "test": "6_export_artifact_download",
    "status": "PASS",
    "payload": {
      "export": {
        "graph_id": "smoke-tiny-r3",
        "format": "zip",
        "artifact_token": "eyJleHAiOjE3ODE3MDUzMjQsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMyIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMy9ncmFwaGlmeS1vdXQuemlwIn0._fx0HPKBS19az6ScTO2jgCkepITHS7-nDQt9mF-Lkug",
        "artifact_url": "/v1/graphify/artifacts/eyJleHAiOjE3ODE3MDUzMjQsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yMyIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yMy9ncmFwaGlmeS1vdXQuemlwIn0._fx0HPKBS19az6ScTO2jgCkepITHS7-nDQt9mF-Lkug",
        "expires_in_seconds": 900
      },
      "bytes": 8392
    }
  },
  {
    "test": "7_update_existing_graph_id",
    "status": "PASS",
    "payload": {
      "job_id": "e9c6e69a5194409f",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r3",
      "message": "completed"
    }
  }
]
```

## Round 4

# Graphify Backend 5x Test Report

- Base URL: `http://127.0.0.1:8765`
- Fixture: `/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo`

| No | Test | Status |
|---:|---|---|
| 1 | 1_health | PASS |
| 2 | 2_build_local_fixture | PASS |
| 3 | 3_stats_persistent_graph | PASS |
| 4 | 4_query_returns_hits | PASS |
| 5 | 5_path_explain_affected | PASS |
| 6 | 6_export_artifact_download | PASS |
| 7 | 7_update_existing_graph_id | PASS |

## Raw Results
```json
[
  {
    "test": "1_health",
    "status": "PASS",
    "payload": {
      "status": "ok",
      "auth_mode": "none",
      "data_dir": "/mnt/data/graphify_full_stack_ready/backend/data_test",
      "allowed_hosts": [
        "github.com",
        "codeload.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com"
      ],
      "run_mode": "worker"
    }
  },
  {
    "test": "2_build_local_fixture",
    "status": "PASS",
    "payload": {
      "job_id": "8a305ea8dcec43fa",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r4",
      "message": "completed"
    }
  },
  {
    "test": "3_stats_persistent_graph",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r4",
      "nodes": 20,
      "edges": 24,
      "files": 5,
      "symbols": 11,
      "skipped_files": 0,
      "generated_at": "2026-06-17T13:53:45.837705+00:00",
      "source": {
        "type": "local_path",
        "url": null,
        "branch": null,
        "path": "/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo"
      }
    }
  },
  {
    "test": "4_query_returns_hits",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r4",
      "query": "invoice validate shipment",
      "hits": [
        {
          "node_id": "symbol:src/invoice.py:InvoiceValidator",
          "label": "InvoiceValidator",
          "type": "class",
          "score": 1.8708,
          "evidence": "class InvoiceValidator line 4",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:README.md",
          "label": "README.md",
          "type": "file",
          "score": 1.8371,
          "evidence": "# Tiny Invoice Repo\nThis fixture validates invoice shipment cost logic and Graphify query/path/explain operations.\n## Workflow\n1. Load invoice rows.\n2. Validate shipment amount.",
          "path": "README.md"
        },
        {
          "node_id": "file:src/invoice.py",
          "label": "invoice.py",
          "type": "file",
          "score": 1.4924,
          "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
          "path": "src/invoice.py"
        },
        {
          "node_id": "symbol:src/invoice.py:validate_invoice",
          "label": "validate_invoice",
          "type": "function",
          "score": 1.2649,
          "evidence": "def validate_invoice(...) line 10",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:docs/process.md",
          "label": "process.md",
          "type": "file",
          "score": 1.2511,
          "evidence": "# Shipment Validation Process\n## Invoice Evidence\nCI/PL, BL, BOE, DO and delivery note must match the invoice claim.\n## Affected Analysis",
          "path": "docs/process.md"
        }
      ]
    }
  },
  {
    "test": "5_path_explain_affected",
    "status": "PASS",
    "payload": {
      "path": {
        "graph_id": "smoke-tiny-r4",
        "found": true,
        "path": [
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/8a305ea8dcec43fa/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a305ea8dcec43fa",
              "src"
            ]
          },
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "symbol:src/invoice.py:validate_invoice",
            "type": "function",
            "label": "validate_invoice",
            "path": "src/invoice.py",
            "line": 10,
            "summary": "Python function validate_invoice",
            "evidence": "def validate_invoice(...) line 10",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "validate_invoice",
              "validate_invoice",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "validate_invoice",
              "def",
              "validate_invoice",
              "line"
            ]
          }
        ],
        "edges": [
          {
            "id": "733cfeb352a25873",
            "source": "project:root",
            "target": "file:src/invoice.py",
            "relation": "CONTAINS",
            "evidence": "src/invoice.py"
          },
          {
            "id": "0e920ac02079e8fd",
            "source": "file:src/invoice.py",
            "target": "symbol:src/invoice.py:validate_invoice",
            "relation": "DEFINES",
            "evidence": "line 15"
          }
        ]
      },
      "explain": {
        "graph_id": "smoke-tiny-r4",
        "node": {
          "id": "symbol:src/invoice.py:validate_invoice",
          "type": "function",
          "label": "validate_invoice",
          "path": "src/invoice.py",
          "line": 10,
          "summary": "Python function validate_invoice",
          "evidence": "def validate_invoice(...) line 10",
          "tokens": [
            "symbol",
            "src",
            "invoice",
            "py",
            "validate_invoice",
            "validate_invoice",
            "function",
            "src",
            "invoice",
            "py",
            "python",
            "function",
            "validate_invoice",
            "def",
            "validate_invoice",
            "line"
          ]
        },
        "neighbors": [
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "external:.shipment",
            "type": "external_import",
            "label": ".shipment",
            "summary": "Imported Python module",
            "evidence": "from .shipment import ...",
            "tokens": [
              "external",
              "shipment",
              "shipment",
              "external_import",
              "imported",
              "python",
              "module",
              "from",
              "shipment",
              "import"
            ]
          },
          {
            "id": "symbol:src/invoice.py:InvoiceValidator",
            "type": "class",
            "label": "InvoiceValidator",
            "path": "src/invoice.py",
            "line": 4,
            "summary": "Validates invoice amount and shipment lane evidence.",
            "evidence": "class InvoiceValidator line 4",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "invoicevalidator",
              "invoicevalidator",
              "class",
              "src",
              "invoice",
              "py",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "class",
              "invoicevalidator",
              "line"
            ]
          },
          {
            "id": "symbol:src/invoice.py:__init__",
            "type": "function",
            "label": "__init__",
            "path": "src/invoice.py",
            "line": 7,
            "summary": "Python function __init__",
            "evidence": "def __init__(...) line 7",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "__init__",
              "__init__",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "__init__",
              "def",
              "__init__",
              "line"
            ]
          },
          {
            "id": "file:src/shipment.py",
            "type": "file",
            "label": "shipment.py",
            "path": "src/shipment.py",
            "size_bytes": 232,
            "sha256": "a47d073fedb2627342561d40456e14d6429f01e104024bedf63ba0cf15c84bec",
            "summary": "def normalize_lane(lane: str) -> str: \"\"\"Normalize POL/POD lane string.\"\"\" return lane.strip().upper().replace(\" \", \"-\") def calculate_freight(base: float, surcharge: float) -> float:",
            "evidence": "def normalize_lane(lane: str) -> str:\n\"\"\"Normalize POL/POD lane string.\"\"\"\nreturn lane.strip().upper().replace(\" \", \"-\")\ndef calculate_freight(base: float, surcharge: float) -> float:\nreturn round(base + surcharge, 2)",
            "tokens": [
              "file",
              "src",
              "shipment",
              "py",
              "shipment",
              "py",
              "file",
              "src",
              "shipment",
              "py",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "return",
              "round",
              "base",
              "surcharge"
            ]
          },
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/8a305ea8dcec43fa/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a305ea8dcec43fa",
              "src"
            ]
          },
          {
            "id": "dir:src",
            "type": "directory",
            "label": "src",
            "path": "src",
            "summary": "Directory",
            "tokens": [
              "dir",
              "src",
              "src",
              "directory",
              "src",
              "directory"
            ]
          }
        ],
        "evidence": [
          "def validate_invoice(...) line 10",
          "line 15",
          "line 10",
          "line 1",
          "line 4",
          "line 15",
          "line 7",
          "line 10",
          ".shipment",
          "src/invoice.py",
          "src/invoice.py"
        ],
        "summary": "validate_invoice is a function with 7 neighbor nodes within depth 2."
      },
      "affected_count": 13
    }
  },
  {
    "test": "6_export_artifact_download",
    "status": "PASS",
    "payload": {
      "export": {
        "graph_id": "smoke-tiny-r4",
        "format": "zip",
        "artifact_token": "eyJleHAiOjE3ODE3MDUzMjUsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yNCIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yNC9ncmFwaGlmeS1vdXQuemlwIn0.r2PzFVECzR6ga2elHyc99G99KA1vkLF7HpMmfcDNnGQ",
        "artifact_url": "/v1/graphify/artifacts/eyJleHAiOjE3ODE3MDUzMjUsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yNCIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yNC9ncmFwaGlmeS1vdXQuemlwIn0.r2PzFVECzR6ga2elHyc99G99KA1vkLF7HpMmfcDNnGQ",
        "expires_in_seconds": 900
      },
      "bytes": 8391
    }
  },
  {
    "test": "7_update_existing_graph_id",
    "status": "PASS",
    "payload": {
      "job_id": "2b966e79a84647aa",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r4",
      "message": "completed"
    }
  }
]
```

## Round 5

# Graphify Backend 5x Test Report

- Base URL: `http://127.0.0.1:8765`
- Fixture: `/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo`

| No | Test | Status |
|---:|---|---|
| 1 | 1_health | PASS |
| 2 | 2_build_local_fixture | PASS |
| 3 | 3_stats_persistent_graph | PASS |
| 4 | 4_query_returns_hits | PASS |
| 5 | 5_path_explain_affected | PASS |
| 6 | 6_export_artifact_download | PASS |
| 7 | 7_update_existing_graph_id | PASS |

## Raw Results
```json
[
  {
    "test": "1_health",
    "status": "PASS",
    "payload": {
      "status": "ok",
      "auth_mode": "none",
      "data_dir": "/mnt/data/graphify_full_stack_ready/backend/data_test",
      "allowed_hosts": [
        "github.com",
        "codeload.github.com",
        "raw.githubusercontent.com",
        "objects.githubusercontent.com"
      ],
      "run_mode": "worker"
    }
  },
  {
    "test": "2_build_local_fixture",
    "status": "PASS",
    "payload": {
      "job_id": "63a32d188bcb496a",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r5",
      "message": "completed"
    }
  },
  {
    "test": "3_stats_persistent_graph",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r5",
      "nodes": 20,
      "edges": 24,
      "files": 5,
      "symbols": 11,
      "skipped_files": 0,
      "generated_at": "2026-06-17T13:53:47.295321+00:00",
      "source": {
        "type": "local_path",
        "url": null,
        "branch": null,
        "path": "/mnt/data/graphify_full_stack_ready/backend/tests/fixtures/tiny_repo"
      }
    }
  },
  {
    "test": "4_query_returns_hits",
    "status": "PASS",
    "payload": {
      "graph_id": "smoke-tiny-r5",
      "query": "invoice validate shipment",
      "hits": [
        {
          "node_id": "symbol:src/invoice.py:InvoiceValidator",
          "label": "InvoiceValidator",
          "type": "class",
          "score": 1.8708,
          "evidence": "class InvoiceValidator line 4",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:README.md",
          "label": "README.md",
          "type": "file",
          "score": 1.8371,
          "evidence": "# Tiny Invoice Repo\nThis fixture validates invoice shipment cost logic and Graphify query/path/explain operations.\n## Workflow\n1. Load invoice rows.\n2. Validate shipment amount.",
          "path": "README.md"
        },
        {
          "node_id": "file:src/invoice.py",
          "label": "invoice.py",
          "type": "file",
          "score": 1.4924,
          "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
          "path": "src/invoice.py"
        },
        {
          "node_id": "symbol:src/invoice.py:validate_invoice",
          "label": "validate_invoice",
          "type": "function",
          "score": 1.2649,
          "evidence": "def validate_invoice(...) line 10",
          "path": "src/invoice.py"
        },
        {
          "node_id": "file:docs/process.md",
          "label": "process.md",
          "type": "file",
          "score": 1.2511,
          "evidence": "# Shipment Validation Process\n## Invoice Evidence\nCI/PL, BL, BOE, DO and delivery note must match the invoice claim.\n## Affected Analysis",
          "path": "docs/process.md"
        }
      ]
    }
  },
  {
    "test": "5_path_explain_affected",
    "status": "PASS",
    "payload": {
      "path": {
        "graph_id": "smoke-tiny-r5",
        "found": true,
        "path": [
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/63a32d188bcb496a/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a32d188bcb496a",
              "src"
            ]
          },
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "symbol:src/invoice.py:validate_invoice",
            "type": "function",
            "label": "validate_invoice",
            "path": "src/invoice.py",
            "line": 10,
            "summary": "Python function validate_invoice",
            "evidence": "def validate_invoice(...) line 10",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "validate_invoice",
              "validate_invoice",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "validate_invoice",
              "def",
              "validate_invoice",
              "line"
            ]
          }
        ],
        "edges": [
          {
            "id": "733cfeb352a25873",
            "source": "project:root",
            "target": "file:src/invoice.py",
            "relation": "CONTAINS",
            "evidence": "src/invoice.py"
          },
          {
            "id": "0e920ac02079e8fd",
            "source": "file:src/invoice.py",
            "target": "symbol:src/invoice.py:validate_invoice",
            "relation": "DEFINES",
            "evidence": "line 15"
          }
        ]
      },
      "explain": {
        "graph_id": "smoke-tiny-r5",
        "node": {
          "id": "symbol:src/invoice.py:validate_invoice",
          "type": "function",
          "label": "validate_invoice",
          "path": "src/invoice.py",
          "line": 10,
          "summary": "Python function validate_invoice",
          "evidence": "def validate_invoice(...) line 10",
          "tokens": [
            "symbol",
            "src",
            "invoice",
            "py",
            "validate_invoice",
            "validate_invoice",
            "function",
            "src",
            "invoice",
            "py",
            "python",
            "function",
            "validate_invoice",
            "def",
            "validate_invoice",
            "line"
          ]
        },
        "neighbors": [
          {
            "id": "file:src/invoice.py",
            "type": "file",
            "label": "invoice.py",
            "path": "src/invoice.py",
            "size_bytes": 592,
            "sha256": "a27136199b1a0fa36227f514cb271f75223f47451327987bc85495cc1979b443",
            "summary": "from .shipment import normalize_lane class InvoiceValidator: \"\"\"Validates invoice amount and shipment lane evidence.\"\"\" def __init__(self, tolerance: float = 0.01) -> None:",
            "evidence": "from .shipment import normalize_lane\nclass InvoiceValidator:\n\"\"\"Validates invoice amount and shipment lane evidence.\"\"\"\ndef __init__(self, tolerance: float = 0.01) -> None:\nself.tolerance = tolerance",
            "tokens": [
              "file",
              "src",
              "invoice",
              "py",
              "invoice",
              "py",
              "file",
              "src",
              "invoice",
              "py",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "from",
              "shipment",
              "import",
              "normalize_lane",
              "class",
              "invoicevalidator",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "def",
              "__init__",
              "self",
              "tolerance",
              "float",
              "none",
              "self",
              "tolerance",
              "tolerance"
            ]
          },
          {
            "id": "external:.shipment",
            "type": "external_import",
            "label": ".shipment",
            "summary": "Imported Python module",
            "evidence": "from .shipment import ...",
            "tokens": [
              "external",
              "shipment",
              "shipment",
              "external_import",
              "imported",
              "python",
              "module",
              "from",
              "shipment",
              "import"
            ]
          },
          {
            "id": "symbol:src/invoice.py:InvoiceValidator",
            "type": "class",
            "label": "InvoiceValidator",
            "path": "src/invoice.py",
            "line": 4,
            "summary": "Validates invoice amount and shipment lane evidence.",
            "evidence": "class InvoiceValidator line 4",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "invoicevalidator",
              "invoicevalidator",
              "class",
              "src",
              "invoice",
              "py",
              "validates",
              "invoice",
              "amount",
              "and",
              "shipment",
              "lane",
              "evidence",
              "class",
              "invoicevalidator",
              "line"
            ]
          },
          {
            "id": "symbol:src/invoice.py:__init__",
            "type": "function",
            "label": "__init__",
            "path": "src/invoice.py",
            "line": 7,
            "summary": "Python function __init__",
            "evidence": "def __init__(...) line 7",
            "tokens": [
              "symbol",
              "src",
              "invoice",
              "py",
              "__init__",
              "__init__",
              "function",
              "src",
              "invoice",
              "py",
              "python",
              "function",
              "__init__",
              "def",
              "__init__",
              "line"
            ]
          },
          {
            "id": "file:src/shipment.py",
            "type": "file",
            "label": "shipment.py",
            "path": "src/shipment.py",
            "size_bytes": 232,
            "sha256": "a47d073fedb2627342561d40456e14d6429f01e104024bedf63ba0cf15c84bec",
            "summary": "def normalize_lane(lane: str) -> str: \"\"\"Normalize POL/POD lane string.\"\"\" return lane.strip().upper().replace(\" \", \"-\") def calculate_freight(base: float, surcharge: float) -> float:",
            "evidence": "def normalize_lane(lane: str) -> str:\n\"\"\"Normalize POL/POD lane string.\"\"\"\nreturn lane.strip().upper().replace(\" \", \"-\")\ndef calculate_freight(base: float, surcharge: float) -> float:\nreturn round(base + surcharge, 2)",
            "tokens": [
              "file",
              "src",
              "shipment",
              "py",
              "shipment",
              "py",
              "file",
              "src",
              "shipment",
              "py",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "def",
              "normalize_lane",
              "lane",
              "str",
              "str",
              "normalize",
              "pol",
              "pod",
              "lane",
              "string",
              "return",
              "lane",
              "strip",
              "upper",
              "replace",
              "def",
              "calculate_freight",
              "base",
              "float",
              "surcharge",
              "float",
              "float",
              "return",
              "round",
              "base",
              "surcharge"
            ]
          },
          {
            "id": "project:root",
            "type": "project",
            "label": "src",
            "path": ".",
            "summary": "Repository/project root",
            "evidence": "/mnt/data/graphify_full_stack_ready/backend/data_test/workspaces/63a32d188bcb496a/src",
            "tokens": [
              "project",
              "root",
              "src",
              "project",
              "repository",
              "project",
              "root",
              "mnt",
              "data",
              "graphify_full_stack_ready",
              "backend",
              "data_test",
              "workspaces",
              "a32d188bcb496a",
              "src"
            ]
          },
          {
            "id": "dir:src",
            "type": "directory",
            "label": "src",
            "path": "src",
            "summary": "Directory",
            "tokens": [
              "dir",
              "src",
              "src",
              "directory",
              "src",
              "directory"
            ]
          }
        ],
        "evidence": [
          "def validate_invoice(...) line 10",
          "line 15",
          "line 10",
          "line 1",
          "line 4",
          "line 15",
          "line 7",
          "line 10",
          ".shipment",
          "src/invoice.py",
          "src/invoice.py"
        ],
        "summary": "validate_invoice is a function with 7 neighbor nodes within depth 2."
      },
      "affected_count": 13
    }
  },
  {
    "test": "6_export_artifact_download",
    "status": "PASS",
    "payload": {
      "export": {
        "graph_id": "smoke-tiny-r5",
        "format": "zip",
        "artifact_token": "eyJleHAiOjE3ODE3MDUzMjcsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yNSIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yNS9ncmFwaGlmeS1vdXQuemlwIn0.8Xiw8jEneOJ3Y3B_cfSMakNCzwsPYwoSffzjWNrhhuA",
        "artifact_url": "/v1/graphify/artifacts/eyJleHAiOjE3ODE3MDUzMjcsImZvcm1hdCI6InppcCIsImdyYXBoX2lkIjoic21va2UtdGlueS1yNSIsInBhdGgiOiIvbW50L2RhdGEvZ3JhcGhpZnlfZnVsbF9zdGFja19yZWFkeS9iYWNrZW5kL2RhdGFfdGVzdC9hcnRpZmFjdHMvc21va2UtdGlueS1yNS9ncmFwaGlmeS1vdXQuemlwIn0.8Xiw8jEneOJ3Y3B_cfSMakNCzwsPYwoSffzjWNrhhuA",
        "expires_in_seconds": 900
      },
      "bytes": 8390
    }
  },
  {
    "test": "7_update_existing_graph_id",
    "status": "PASS",
    "payload": {
      "job_id": "e3e524af78ca41de",
      "status": "succeeded",
      "graph_id": "smoke-tiny-r5",
      "message": "completed"
    }
  }
]
```
