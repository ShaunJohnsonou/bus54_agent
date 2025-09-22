import streamlit as st


def realocate_cpu_resources(doner_list: list[tuple[str, float]], receiver_list: list[tuple[str, float]]) -> str:
    '''
    This function takes a list of donor servers with their CPU utilization and a list of receiver servers
    with their CPU utilization, then dynamically reallocates CPU resources from donors to receivers.
    
    Args:
        doner_list: List of tuples with (server_name, cpu_utilization)
        receiver_list: List of tuples with (server_name, cpu_utilization)
        
    Returns:
        str: JSON-formatted reallocation plan
    '''
    import json
    
    # Initialize the reallocation plan
    reallocation_plan = {
        "reallocation": [],
        "summary": {
            "total_cores_moved": 0,
            "donor_servers": len(doner_list),
            "receiver_servers": len(receiver_list)
        }
    }
    
    # Sort donors by CPU utilization (ascending - lowest utilization first)
    sorted_donors = sorted(doner_list, key=lambda x: x[1])
    
    # Sort receivers by CPU utilization (descending - highest utilization first)
    sorted_receivers = sorted(receiver_list, key=lambda x: x[1], reverse=True)
    
    # Simple allocation strategy:
    # 1. Start with neediest receivers
    # 2. Allocate more cores to servers with higher utilization
    # 3. Take more cores from servers with lower utilization
    
    available_cores_per_donor = {}
    for donor_name, donor_util in sorted_donors:
        # Estimate available cores based on utilization
        # Lower utilization = more cores available to donate
        if donor_util < 10:
            available_cores = 3  # Very low utilization, can donate more
        elif donor_util < 20:
            available_cores = 2  # Low utilization
        else:
            available_cores = 1  # Moderate utilization
        
        available_cores_per_donor[donor_name] = available_cores
    
    total_cores_moved = 0
    current_donor_idx = 0
    
    # Allocate cores to receivers based on utilization
    for receiver_name, receiver_util in sorted_receivers:
        # Determine how many cores this receiver needs
        cores_needed = 0
        rationale = ""
        
        if receiver_util > 95:
            cores_needed = 2
            rationale = "Critical high utilization"
        elif receiver_util > 85:
            cores_needed = 1
            rationale = "High utilization"
        elif receiver_util > 75:
            cores_needed = 1
            rationale = "Elevated utilization"
        
        # Skip if no cores needed
        if cores_needed == 0:
            continue
        
        # Try to allocate from available donors
        cores_allocated = 0
        while cores_allocated < cores_needed and current_donor_idx < len(sorted_donors):
            donor_name = sorted_donors[current_donor_idx][0]
            
            if available_cores_per_donor[donor_name] > 0:
                # Allocate one core from this donor
                cores_to_move = min(cores_needed - cores_allocated, available_cores_per_donor[donor_name])
                available_cores_per_donor[donor_name] -= cores_to_move
                
                reallocation_plan["reallocation"].append({
                    "action": f"Move {cores_to_move} core{'s' if cores_to_move > 1 else ''}",
                    "from": donor_name,
                    "to": receiver_name,
                    "cores": cores_to_move,
                    "rationale": rationale
                })
                
                cores_allocated += cores_to_move
                total_cores_moved += cores_to_move
                
                # If this donor has no more cores to give, move to next donor
                if available_cores_per_donor[donor_name] == 0:
                    current_donor_idx += 1
            else:
                # This donor has no more cores to give, move to next donor
                current_donor_idx += 1
    
    # Update summary
    reallocation_plan["summary"]["total_cores_moved"] = total_cores_moved
    reallocation_plan["summary"]["result"] = f"Reallocated {total_cores_moved} cores from {len(doner_list)} donors to {len(receiver_list)} receivers"
    
    # Return the plan as a JSON string
    return json.dumps(reallocation_plan)


def calculate_cost(resource_type: str, quantity: int) -> float:
    '''
    Calculates the monetary cost of allocating server resources for billing purposes.
    
    This MCP function computes the cost based on resource type and quantity allocated.
    Used by the Management Control Plane to track expenses across resource allocations,
    optimize budget utilization, and provide cost estimates for resource reallocation
    operations.
    
    Args:
        resource_type: Type of resource being calculated ("cpu", "memory", or "disk")
        quantity: Amount of resource units (cores for CPU, GB for memory, TB for disk)
        
    Returns:
        float: The calculated cost in dollars per hour
              Returns -1 if resource_type is not recognized
              
    Examples:
        >>> calculate_cost("cpu", 4)
        0.4  # $0.40 per hour for 4 CPU cores
        
        >>> calculate_cost("memory", 16)
        0.8  # $0.80 per hour for 16GB memory
    '''
    # Cost calculation based on resource type
    # Rates are defined in dollars per unit per hour
    if resource_type.lower() == "cpu":
        return quantity * 0.1  # $0.10 per CPU core per hour
    elif resource_type.lower() == "memory":
        return quantity * 0.05  # $0.05 per GB of memory per hour
    elif resource_type.lower() == "disk":
        return quantity * 0.02  # $0.02 per TB of disk per hour
    return -1  # Invalid resource type