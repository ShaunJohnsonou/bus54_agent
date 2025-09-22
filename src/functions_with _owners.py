import datetime
import json
import os
from typing import Any, Dict

# Global variable to cache the static data
_static_data = None

def load_static_data():
    """Load static server data from JSON file."""
    global _static_data
    if _static_data is None:
        # Get the directory of the current file and navigate to data folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        data_file = os.path.join(parent_dir, 'data', 'static_server_data.json')
        
        try:
            with open(data_file, 'r') as f:
                _static_data = json.load(f)
        except FileNotFoundError:
            # Fallback to empty data structure if file not found
            _static_data = {"servers": [], "feature_coverage": {}, "memory_features_by_server": {}}
    
    return _static_data


def format_json_for_display(data: Dict[str, Any]) -> str:
    """
    Format JSON data for better display in chat UI.
    Returns a properly indented JSON string.
    """
    return json.dumps(data, indent=2, default=str)

def get_run_info(run_dir=None):
    """
    Lightweight health & freshness. Returns shapes and provenance.
    """
    # Use static run directory for consistent results
    run_directory = run_dir if run_dir else "run_20250911_120000"
    static_timestamp = "2025-09-11T12:00:00"
    
    return {
        "status": "success",
        "run_dir": run_directory,
        "shapes": {
            "servers": 150,
            "cpu_metrics": 145,
            "memory_metrics": 132,
            "disk_metrics": 128
        },
        "provenance": {
            "created_at": static_timestamp,
            "data_sources": ["telemetry_metrics", "server_inventory", "anomaly_issues"],
            "freshness_hours": 4
        }
    }

def list_servers(run_dir=None, limit=20, offset=0, fields=None):
    """
    Enumerate servers with readiness flags and headline CPU.
    """
    if fields is None:
        fields = ["server", "has_cpu", "has_disk", "has_mem_bytes", "has_mem_util", 
                 "cpu_util_avg", "cpu_util_p95", "cpu_underutilized_flag", "cpu_overstressed_flag",
                 "owner", "team", "manager", "department"]
    
    # Load static server data
    static_data = load_static_data()
    all_servers = static_data.get("servers", [])
    
    # Apply pagination
    paginated = all_servers[offset:offset+limit]
    
    # Filter fields if specified
    if fields:
        filtered_servers = []
        for server in paginated:
            filtered_server = {field: server.get(field) for field in fields if field in server}
            filtered_servers.append(filtered_server)
        paginated = filtered_servers
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "total": len(all_servers),
        "items": paginated,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        }
    }

def underutilized_servers(run_dir=None, limit=20, offset=0, avg_lt=10.0, p95_lt=30.0, 
                         require_both=True, servers=None, exclude_servers=None, fields=None):
    """
    Find potential donors (likely over-provisioned).
    """
    if fields is None:
        fields = ["server", "cpu_util_avg", "cpu_util_p95", "cpu_cores_inferred", 
                 "has_mem_bytes", "has_mem_util", "has_disk", "cpu_underutilized_flag"]
    
    if servers is None:
        servers = []
    
    if exclude_servers is None:
        exclude_servers = []
    
    # Get all servers
    all_servers_result = list_servers(run_dir, 100, 0)
    all_servers = all_servers_result["items"]
    
    # Filter for underutilized
    underutilized = []
    for server in all_servers:
        # Skip if in exclude list
        if server["server"] in exclude_servers:
            continue
        
        # Skip if servers list provided and not in it
        if servers and server["server"] not in servers:
            continue
        
        avg_check = server["cpu_util_avg"] < avg_lt
        p95_check = server["cpu_util_p95"] < p95_lt
        
        if require_both and avg_check and p95_check:
            underutilized.append(server)
        elif not require_both and (avg_check or p95_check):
            underutilized.append(server)
    
    # Apply pagination
    paginated = underutilized[offset:offset+limit]
    
    # Filter fields if specified
    if fields:
        filtered_servers = []
        for server in paginated:
            filtered_server = {field: server.get(field) for field in fields if field in server}
            filtered_servers.append(filtered_server)
        paginated = filtered_servers
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "criteria": {
            "avg_lt": avg_lt,
            "p95_lt": p95_lt,
            "require_both": require_both
        },
        "total": len(underutilized),
        "items": paginated,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        },
        "notes": [
            "These servers are candidates for resource reduction or reallocation",
            "Consider reviewing application requirements before making changes"
        ]
    }

def overstressed_servers(run_dir=None, limit=20, offset=0, avg_gt=70.0, p95_gt=90.0,
                        require_any=True, servers=None, exclude_servers=None, fields=None):
    """
    Find potential receivers (likely constrained).
    """
    if fields is None:
        fields = ["server", "cpu_util_avg", "cpu_util_p95", "has_mem_bytes", 
                 "has_mem_util", "has_disk", "cpu_overstressed_flag"]
    
    if servers is None:
        servers = []
    
    if exclude_servers is None:
        exclude_servers = []
    
    # Get all servers
    all_servers_result = list_servers(run_dir, 100, 0)
    all_servers = all_servers_result["items"]
    
    # Filter for overstressed
    overstressed = []
    for server in all_servers:
        # Skip if in exclude list
        if server["server"] in exclude_servers:
            continue
        
        # Skip if servers list provided and not in it
        if servers and server["server"] not in servers:
            continue
        
        avg_check = server["cpu_util_avg"] > avg_gt
        p95_check = server["cpu_util_p95"] > p95_gt
        
        if require_any and (avg_check or p95_check):
            overstressed.append(server)
        elif not require_any and avg_check and p95_check:
            overstressed.append(server)
    
    # Apply pagination
    paginated = overstressed[offset:offset+limit]
    
    # Filter fields if specified
    if fields:
        filtered_servers = []
        for server in paginated:
            filtered_server = {field: server.get(field) for field in fields if field in server}
            filtered_servers.append(filtered_server)
        paginated = filtered_servers
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "criteria": {
            "avg_gt": avg_gt,
            "p95_gt": p95_gt,
            "require_any": require_any
        },
        "total": len(overstressed),
        "items": paginated,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        },
        "notes": [
            "These servers may benefit from additional resources or workload rebalancing",
            "Consider investigating application performance issues"
        ]
    }

def memory_coverage(run_dir=None, limit=50, offset=0, fields=None):
    """
    Show which servers have memory-byte coverage and mem util present.
    """
    if fields is None:
        fields = ["server", "mem_byte_features_present", "has_mem_bytes", "has_mem_util"]
    
    # Get all servers
    all_servers_result = list_servers(run_dir, 100, 0)
    all_servers = all_servers_result["items"]
    
    # Enhance with memory coverage information from static data
    static_data = load_static_data()
    memory_features_by_server = static_data.get("memory_features_by_server", {})
    
    for server in all_servers:
        server_id = server.get("server")
        server["mem_byte_features_present"] = memory_features_by_server.get(server_id, [])
    
    # Apply pagination
    paginated = all_servers[offset:offset+limit]
    
    # Filter fields if specified
    if fields:
        filtered_servers = []
        for server in paginated:
            filtered_server = {field: server.get(field) for field in fields if field in server}
            filtered_servers.append(filtered_server)
        paginated = filtered_servers
    
    # Calculate summary
    summary = {
        "total_servers": len(all_servers),
        "has_mem_bytes": sum(1 for s in all_servers if s.get("has_mem_bytes")),
        "has_mem_util": sum(1 for s in all_servers if s.get("has_mem_util")),
        "has_both": sum(1 for s in all_servers if s.get("has_mem_bytes") and s.get("has_mem_util")),
        "has_neither": sum(1 for s in all_servers if not s.get("has_mem_bytes") and not s.get("has_mem_util"))
    }
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "summary": summary,
        "total": len(all_servers),
        "items": paginated,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        }
    }

def server_detail(run_dir=None, server=None, fields=None):
    """
    Single-server drilldown for answer citations.
    """
    if server is None:
        return {"status": "error", "message": "Server parameter is required"}
    
    if fields is None:
        fields = ["server", "cpu_util_avg", "cpu_util_p95", "cpu_underutilized_flag", "cpu_overstressed_flag",
                 "cpu_cores_inferred", "cpu_core_inference_method", "mem_util_avg", "mem_util_p95", 
                 "has_mem", "mem_source", "disk_free_pct_median", "disk_free_pct_min", 
                 "disks_overalloc_count", "disks_low_free_count", "owner", "team", "manager", "department"]
    
    # Load static server data
    static_data = load_static_data()
    all_servers = static_data.get("servers", [])
    
    # Find the requested server
    server_details = None
    for srv in all_servers:
        if srv.get("server") == server:
            server_details = srv.copy()
            break
    
    if server_details is None:
        return {"status": "error", "message": f"Server '{server}' not found"}
    
    # Filter fields if specified
    if fields:
        filtered_details = {field: server_details.get(field) for field in fields if field in server_details}
        server_details = filtered_details
    
    # Calculate coverage based on server data
    coverage = {
        "cpu": server_details.get("has_cpu", True),
        "memory": server_details.get("has_mem", False),
        "disk": server_details.get("has_disk", False),
        "network": True  # Assume network is always available for simplicity
    }
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "item": server_details,
        "coverage": coverage,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        }
    }

def reallocation_candidates(run_dir=None, donor_limit=5, receiver_limit=5, 
                           donor_avg_lt=10.0, donor_p95_lt=30.0, donor_require_both=True,
                           receiver_avg_gt=70.0, receiver_p95_gt=90.0, receiver_require_any=True):
    """
    Data-only donor/receiver lists; the model writes the recommendation.
    """
    # Get donor candidates
    donors = underutilized_servers(
        run_dir=run_dir,
        limit=donor_limit,
        avg_lt=donor_avg_lt,
        p95_lt=donor_p95_lt,
        require_both=donor_require_both
    )
    
    # Get receiver candidates
    receivers = overstressed_servers(
        run_dir=run_dir,
        limit=receiver_limit,
        avg_gt=receiver_avg_gt,
        p95_gt=receiver_p95_gt,
        require_any=receiver_require_any
    )
    
    # Format donor and receiver information for better display
    # Extract only what's needed from the nested structure
    formatted_donors = []
    for donor in donors.get("items", []):
        formatted_donors.append({
            "server": donor.get("server"),
            "cpu_util_avg": f"{donor.get('cpu_util_avg', 0):.1f}%",
            "cpu_util_p95": f"{donor.get('cpu_util_p95', 0):.1f}%",
            "has_mem": "✓" if donor.get("has_mem_bytes") else "✗",
            "has_disk": "✓" if donor.get("has_disk") else "✗"
        })
    
    formatted_receivers = []
    for receiver in receivers.get("items", []):
        formatted_receivers.append({
            "server": receiver.get("server"),
            "cpu_util_avg": f"{receiver.get('cpu_util_avg', 0):.1f}%",
            "cpu_util_p95": f"{receiver.get('cpu_util_p95', 0):.1f}%",
            "has_mem": "✓" if receiver.get("has_mem_bytes") else "✗",
            "has_disk": "✓" if receiver.get("has_disk") else "✗"
        })
    
    # Create a deterministic timestamp for consistent output
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    result = {
        "status": "success",
        "summary": {
            "donor_count": donors.get("total", 0),
            "receiver_count": receivers.get("total", 0),
            "donor_criteria": donors.get("criteria", {}),
            "receiver_criteria": receivers.get("criteria", {})
        },
        "donors": formatted_donors,
        "receivers": formatted_receivers,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        },
        "notes": [
            "Consider moving resources from underutilized servers to overutilized ones",
            "Always test performance after resource reallocation"
        ]
    }
    
    # Add full data for further processing if needed
    result["_raw_data"] = {
        "donors": donors,
        "receivers": receivers
    }
    
    return result

def feature_coverage(run_dir=None, server=None, feature_prefix=None, limit=100, offset=0):
    """
    Explain missing metrics by listing coverage rows.
    """
    if server is None and feature_prefix is None:
        return {"status": "error", "message": "Either server or feature_prefix parameter is required"}
    
    # Load static feature coverage data
    static_data = load_static_data()
    feature_coverage_data = static_data.get("feature_coverage", {})
    
    # Get all feature categories
    all_feature_categories = ["cpu_features", "memory_features", "disk_features", "network_features"]
    all_features = []
    
    # Collect all features from the static data
    for category in all_feature_categories:
        if category in feature_coverage_data:
            all_features.extend(list(feature_coverage_data[category].keys()))
    
    # Filter by prefix if provided
    if feature_prefix:
        filtered_features = [f for f in all_features if f.startswith(feature_prefix)]
    else:
        filtered_features = all_features
    
    # Generate coverage data based on static information
    coverage_items = []
    for feature in filtered_features:
        # Find which category this feature belongs to
        feature_info = None
        for category in all_feature_categories:
            if category in feature_coverage_data and feature in feature_coverage_data[category]:
                feature_info = feature_coverage_data[category][feature]
                break
        
        if feature_info:
            if server:
                # Check if specific server has this feature
                is_present = server in feature_info.get("servers_with_data", [])
                item = {
                    "server": server,
                    "feature": feature,
                    "is_present": is_present,
                    "last_seen": datetime.datetime.now().isoformat() if is_present else None,
                    "data_points": feature_info.get("data_points", 0) // len(feature_info.get("servers_with_data", [1])) if is_present else 0
                }
                coverage_items.append(item)
            else:
                # Show coverage for all servers that have this feature
                for srv in feature_info.get("servers_with_data", []):
                    item = {
                        "server": srv,
                        "feature": feature,
                        "is_present": True,
                        "last_seen": datetime.datetime.now().isoformat(),
                        "data_points": feature_info.get("data_points", 0) // len(feature_info.get("servers_with_data", [1]))
                    }
                    coverage_items.append(item)
    
    # Apply pagination
    paginated = coverage_items[offset:offset+limit]
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "total": len(coverage_items),
        "items": paginated,
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        }
    }

def person_server_ownership(person_name=None, run_dir=None):
    """
    Get server ownership count for a person, including direct servers and servers owned by subordinates.
    
    Args:
        person_name (str): Full name of the person (e.g., "Alex Thompson", "Mike Rodriguez")
        run_dir (str): Run directory (optional)
        
    Returns:
        dict: Contains direct server count, subordinate server count, and detailed breakdowns
    """
    if person_name is None:
        return {"status": "error", "message": "Person name parameter is required"}
    
    # Load static server data
    static_data = load_static_data()
    all_servers = static_data.get("servers", [])
    org_structure = static_data.get("organizational_structure", {})
    
    # Find person in organizational structure
    person_info = None
    person_key = None
    
    # Check senior manager
    senior_mgr = org_structure.get("senior_infrastructure_manager", {})
    if senior_mgr.get("name") == person_name:
        person_info = senior_mgr
        person_key = "senior_infrastructure_manager"
    
    # Check team leads
    if not person_info:
        team_leads = org_structure.get("team_leads", {})
        for key, lead in team_leads.items():
            if lead.get("name") == person_name:
                person_info = lead
                person_key = f"team_leads.{key}"
                break
    
    # Check individual contributors
    if not person_info:
        contributors = org_structure.get("individual_contributors", {})
        for key, contributor in contributors.items():
            if contributor.get("name") == person_name:
                person_info = contributor
                person_key = f"individual_contributors.{key}"
                break
    
    if not person_info:
        return {"status": "error", "message": f"Person '{person_name}' not found in organizational structure"}
    
    # Count direct servers owned by this person
    direct_servers = []
    for server in all_servers:
        if server.get("owner") == person_name:
            direct_servers.append(server["server"])
    
    # Find all subordinates and their servers
    subordinate_servers = {}
    subordinate_total = 0
    
    def get_subordinates(person_manages):
        """Recursively find all people managed by this person."""
        subordinates = []
        if not person_manages:
            return subordinates
            
        for managed_person in person_manages:
            subordinates.append(managed_person)
            
            # Find this person's info to see who they manage
            managed_person_info = None
            
            # Check team leads
            team_leads = org_structure.get("team_leads", {})
            for lead in team_leads.values():
                if lead.get("name") == managed_person:
                    managed_person_info = lead
                    break
            
            # Check individual contributors  
            if not managed_person_info:
                contributors = org_structure.get("individual_contributors", {})
                for contributor in contributors.values():
                    if contributor.get("name") == managed_person:
                        managed_person_info = contributor
                        break
            
            # Recursively get their subordinates
            if managed_person_info and "manages" in managed_person_info:
                subordinates.extend(get_subordinates(managed_person_info["manages"]))
                
        return subordinates
    
    # Get all subordinates
    all_subordinates = get_subordinates(person_info.get("manages", []))
    
    # Count servers for each subordinate
    for subordinate_name in all_subordinates:
        subordinate_server_list = []
        for server in all_servers:
            if server.get("owner") == subordinate_name:
                subordinate_server_list.append(server["server"])
                subordinate_total += 1
        
        if subordinate_server_list:  # Only include if they have servers
            subordinate_servers[subordinate_name] = subordinate_server_list
    
    # Calculate totals
    total_servers_under_management = len(direct_servers) + subordinate_total
    
    return {
        "status": "success",
        "person": {
            "name": person_name,
            "title": person_info.get("title", "Unknown"),
            "team": person_info.get("team", "Unknown"),
            "department": person_info.get("department", "Unknown")
        },
        "direct_ownership": {
            "server_count": len(direct_servers),
            "servers": direct_servers
        },
        "subordinate_ownership": {
            "total_subordinate_servers": subordinate_total,
            "subordinate_count": len(subordinate_servers),
            "servers_by_subordinate": subordinate_servers
        },
        "summary": {
            "total_servers_managed": total_servers_under_management,
            "direct_servers": len(direct_servers),
            "subordinate_servers": subordinate_total,
            "people_managed": len(all_subordinates)
        },
        "provenance": {
            "run_dir": run_dir if run_dir else f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.datetime.now().isoformat()
        }
    }

def list_server_owners(run_dir=None, include_details=True, sort_by="name"):
    """
    List all people who own servers, with optional detailed information.
    
    Args:
        run_dir (str): Run directory (optional)
        include_details (bool): Include organizational details like title, team, department
        sort_by (str): Sort order - "name", "server_count", "team", or "title"
        
    Returns:
        dict: Contains list of all server owners with their details and server counts
    """
    # Load static server data
    static_data = load_static_data()
    all_servers = static_data.get("servers", [])
    org_structure = static_data.get("organizational_structure", {})
    
    # Collect unique owner names and their server counts
    owner_servers = {}
    for server in all_servers:
        owner = server.get("owner")
        if owner:
            if owner not in owner_servers:
                owner_servers[owner] = []
            owner_servers[owner].append(server["server"])
    
    # Build detailed owner information
    owners_list = []
    for owner_name, server_list in owner_servers.items():
        owner_info = {
            "name": owner_name,
            "server_count": len(server_list),
            "servers": server_list
        }
        
        if include_details:
            # Find organizational details for this person
            person_details = None
            
            # Check senior manager
            senior_mgr = org_structure.get("senior_infrastructure_manager", {})
            if senior_mgr.get("name") == owner_name:
                person_details = senior_mgr
            
            # Check team leads
            if not person_details:
                team_leads = org_structure.get("team_leads", {})
                for lead in team_leads.values():
                    if lead.get("name") == owner_name:
                        person_details = lead
                        break
            
            # Check individual contributors
            if not person_details:
                contributors = org_structure.get("individual_contributors", {})
                for contributor in contributors.values():
                    if contributor.get("name") == owner_name:
                        person_details = contributor
                        break
            
            # Add organizational details
            if person_details:
                owner_info.update({
                    "title": person_details.get("title", "Unknown"),
                    "team": person_details.get("team", "Unknown"), 
                    "department": person_details.get("department", "Unknown"),
                    "email": person_details.get("email", "Unknown"),
                    "phone": person_details.get("phone", "Unknown"),
                    "reports_to": person_details.get("reports_to", "Unknown"),
                    "seniority": person_details.get("seniority", "Unknown")
                })
            else:
                # Fallback for unknown person
                owner_info.update({
                    "title": "Unknown",
                    "team": "Unknown",
                    "department": "Unknown", 
                    "email": "Unknown",
                    "phone": "Unknown",
                    "reports_to": "Unknown",
                    "seniority": "Unknown"
                })
        
        owners_list.append(owner_info)
    
    # Sort the list based on sort_by parameter
    if sort_by == "name":
        owners_list.sort(key=lambda x: x["name"])
    elif sort_by == "server_count":
        owners_list.sort(key=lambda x: x["server_count"], reverse=True)
    elif sort_by == "team":
        owners_list.sort(key=lambda x: x.get("team", "ZZZ"))  # ZZZ puts unknown at end
    elif sort_by == "title":
        owners_list.sort(key=lambda x: x.get("title", "ZZZ"))
    else:
        # Default to name sorting if invalid sort_by provided
        owners_list.sort(key=lambda x: x["name"])
    
    # Calculate summary statistics
    total_owners = len(owners_list)
    total_servers = sum(owner["server_count"] for owner in owners_list)
    avg_servers_per_owner = total_servers / total_owners if total_owners > 0 else 0
    
    # Group by teams for summary
    team_summary = {}
    if include_details:
        for owner in owners_list:
            team = owner.get("team", "Unknown")
            if team not in team_summary:
                team_summary[team] = {"owners": 0, "servers": 0}
            team_summary[team]["owners"] += 1
            team_summary[team]["servers"] += owner["server_count"]
    
    # Use static values for consistent results
    static_timestamp = "2025-09-11T12:00:00"
    static_run_dir = run_dir if run_dir else "run_20250911_120000"
    
    return {
        "status": "success",
        "summary": {
            "total_owners": total_owners,
            "total_servers": total_servers,
            "average_servers_per_owner": round(avg_servers_per_owner, 2),
            "team_breakdown": team_summary if include_details else {}
        },
        "owners": owners_list,
        "metadata": {
            "include_details": include_details,
            "sort_by": sort_by,
            "fields_included": ["name", "server_count", "servers"] + (
                ["title", "team", "department", "email", "phone", "reports_to", "seniority"] 
                if include_details else []
            )
        },
        "provenance": {
            "run_dir": static_run_dir,
            "generated_at": static_timestamp
        }
    }