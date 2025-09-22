def manifest():
    return {
        "name": "server resource management",
        "relevant database names": ["telemetry_metrics", "server_inventory", "anomaly_issues"],
        "description": "Monitor and manage server resources via MCP",
        "version": "1.0",
        "actions": {
            "get_underutilized_servers": {
                "description": "Find servers with resource utilization below the threshold.",
                "parameters": {
                    "resource": {"type": "string", "description": "Resource type ('cpu', 'memory', 'disk')"},
                    "threshold": {"type": "number", "description": "Utilization threshold (0.0-1.0) to identify underutilized servers"}
                }
            },
            "get_overutilized_servers": {
                "description": "Find servers with resource utilization above the threshold.",
                "parameters": {
                    "resource": {"type": "string", "description": "Resource type ('cpu', 'memory', 'disk')"},
                    "threshold": {"type": "number", "description": "Utilization threshold (0.0-1.0) to identify overutilized servers"}
                }
            },
            "get_deallocatable_resources": {
                "description": "Calculate deallocatable resources for underutilized servers.",
                "parameters": {
                    "resource": {"type": "string", "description": "Resource type ('cpu', 'memory', 'disk')"},
                    "threshold": {"type": "number", "description": "Utilization threshold to identify underutilized servers"},
                    "reclaim_ratio": {"type": "number", "description": "Percentage of unused resources that can be reclaimed"}
                }
            },
            "get_current_utilization": {
                "description": "Get current utilization of a specific resource for servers.",
                "parameters": {
                    "resource": {"type": "string", "description": "Resource type ('cpu', 'memory', 'disk')"},
                    "servers": {"type": "array", "items": {"type": "string"}, "description": "List of hostnames to check (optional)"}
                }
            },
            "get_memory_usage_trend": {
                "description": "Get memory usage trend for a specific server over time.",
                "parameters": {
                    "server": {"type": "string", "description": "Hostname of the server"},
                    "days": {"type": "integer", "description": "Number of days to look back"}
                }
            },
            "get_breaching_hosts": {
                "description": "Get hosts that breach the specified thresholds.",
                "parameters": {
                    "thresholds": {
                        "type": "object", 
                        "description": "Dictionary mapping resource types to threshold values (e.g. {'cpu_usage': 90.0, 'mem_used': 80.0, 'disk_used': 85.0})"
                    }
                }
            },
            "get_servicenow_flags": {
                "description": "Get ServiceNow flags for servers with issues.",
                "parameters": {
                    "since_hours": {"type": "integer", "description": "Hours to look back for issues"}
                }
            }
        }
    }

def get_all_functions():
    return {

        "list_servers": {
            "purpose": "Enumerate servers with readiness flags and headline CPU.",
            "parameters": {
                "run_dir": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 20},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "fields": {"type": "array", "items": {"type": "string"}}
            }
        },
        "underutilized_servers": {
            "purpose": "Find potential donors (likely over-provisioned).",
            "parameters": {
                "run_dir": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "offset": {"type": "integer", "default": 0},
                "avg_lt": {"type": "number", "default": 10.0},
                "p95_lt": {"type": "number", "default": 30.0},
                "require_both": {"type": "boolean", "default": True},
                "servers": {"type": "array", "items": {"type": "string"}},
                "exclude_servers": {"type": "array", "items": {"type": "string"}},
                "fields": {"type": "array", "items": {"type": "string"}}
            }
        },
        "overstressed_servers": {
            "purpose": "Find potential receivers (likely constrained).",
            "parameters": {
                "run_dir": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "offset": {"type": "integer", "default": 0},
                "avg_gt": {"type": "number", "default": 70.0},
                "p95_gt": {"type": "number", "default": 90.0},
                "require_any": {"type": "boolean", "default": True},
                "servers": {"type": "array", "items": {"type": "string"}},
                "exclude_servers": {"type": "array", "items": {"type": "string"}},
                "fields": {"type": "array", "items": {"type": "string"}}
            }
        },
        "memory_coverage": {
            "purpose": "Show which servers have memory-byte coverage and mem util present.",
            "parameters": {
                "run_dir": {"type": "string"},
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0},
                "fields": {"type": "array", "items": {"type": "string"}}
            }
        },
        "server_detail": {
            "purpose": "Single-server drilldown for answer citations.",
            "parameters": {
                "run_dir": {"type": "string"},
                "server": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "string"}}
            }
        },
        "reallocation_candidates": {
            "purpose": "Data-only donor/receiver lists; the model writes the recommendation.",
            "parameters": {
                "run_dir": {"type": "string"},
                "donor_limit": {"type": "integer", "default": 5},
                "receiver_limit": {"type": "integer", "default": 5},
                "donor_avg_lt": {"type": "number", "default": 10.0},
                "donor_p95_lt": {"type": "number", "default": 30.0},
                "donor_require_both": {"type": "boolean", "default": True},
                "receiver_avg_gt": {"type": "number", "default": 70.0},
                "receiver_p95_gt": {"type": "number", "default": 90.0},
                "receiver_require_any": {"type": "boolean", "default": True}
            }
        },
        "feature_coverage": {
            "purpose": "Explain missing metrics by listing coverage rows.",
            "parameters": {
                "run_dir": {"type": "string"},
                "server": {"type": "string"},
                "feature_prefix": {"type": "string", "description": "Filter by prefix, e.g. 'wmi_memory_bytes_'"},
                "limit": {"type": "integer", "default": 100},
                "offset": {"type": "integer", "default": 0}
            }
        }
    }


function_manifest = {
    
        "functions": {
            "get_underutilized_servers": {
                "description": "Identify and return a list of servers that have resource utilization (CPU, memory, or disk) below a specified threshold percentage, helping to find servers that may be candidates for resource reallocation or consolidation."
            },
            "get_overutilized_servers": {
                "description": "Identify and return a list of servers that have resource utilization (CPU, memory, or disk) above a specified threshold percentage, helping to find servers that may need additional resources or load balancing."
            },
            "get_deallocatable_resources": {
                "description": "Calculate and return the amount of resources (CPU, memory, or disk) that can be safely deallocated from underutilized servers based on a reclaim ratio, providing insights for resource optimization and cost reduction."
            },
            "get_current_utilization": {
                "description": "Retrieve the current real-time utilization metrics for a specific resource type (CPU, memory, or disk) across all servers or a specified list of servers, providing a snapshot of current system performance."
            },
            "get_memory_usage_trend": {
                "description": "Analyze and return historical memory usage patterns for a specific server over a specified number of days, helping to identify trends, predict future usage, and plan capacity requirements."
            },
            "get_breaching_hosts": {
                "description": "Identify and return servers that exceed specified threshold values for multiple resource types simultaneously, providing a comprehensive view of hosts that may require immediate attention or intervention."
            },
            "get_servicenow_flags": {
                "description": "Retrieve ServiceNow incident flags and alerts for servers that have reported issues or anomalies within a specified time window, helping to correlate performance metrics with known service incidents."
            }
        }
}



def database_schema_manifest():
    return {
        "telemetry_metrics": {
            "schema": {
                "cpu_usage": {"type": "number", "description": "CPU usage percentage"},
                "memory_usage": {"type": "number", "description": "Memory usage percentage"},
                "disk_usage": {"type": "number", "description": "Disk usage percentage"}
            }
        }
    }