from datetime import datetime

# =====================================
# SAMPLE DATA
# =====================================

data = {
    "servers": [
        {
            "name": "Server-A",
            "type": "Production",
            "monthly_cost": 15000,
            "avg_cpu_usage": 12
        },
        {
            "name": "Server-B",
            "type": "Development",
            "monthly_cost": 10000,
            "avg_cpu_usage": 5
        },
        {
            "name": "Server-C",
            "type": "Testing",
            "monthly_cost": 8000,
            "avg_cpu_usage": 60
        }
    ],

    "repos": [
        {
            "name": "Payment-App",
            "language": "Python",
            "last_commit_date": "2025-05-01",
            "commit_count": 300
        },
        {
            "name": "Inventory-App",
            "language": "Java",
            "last_commit_date": "2024-01-10",
            "commit_count": 150
        },
        {
            "name": "Legacy-App",
            "language": "PHP",
            "last_commit_date": "2022-08-15",
            "commit_count": 50
        }
    ],

    "mapping": {
        "Payment-App": "Server-A",
        "Inventory-App": "Server-C",
        "Legacy-App": "Server-B"
    }
}


# =====================================
# ANALYSIS FUNCTIONS
# =====================================

def get_highest_cost_server(data):
    return max(
        data["servers"],
        key=lambda server: server["monthly_cost"]
    )


def get_shutdown_candidate(data):

    low_usage_servers = [
        server
        for server in data["servers"]
        if server["avg_cpu_usage"] < 10
    ]

    if not low_usage_servers:
        return None

    return min(
        low_usage_servers,
        key=lambda server: server["avg_cpu_usage"]
    )


def get_oldest_repository(data):

    return min(
        data["repos"],
        key=lambda repo:
        datetime.strptime(
            repo["last_commit_date"],
            "%Y-%m-%d"
        )
    )


# =====================================
# RESPONSE BUILDERS
# =====================================

def generate_cost_report(data):

    server = get_highest_cost_server(data)

    report = "\n========== COST ANALYSIS ==========\n"
    report += f"{'Server':15}{'Cost':15}{'CPU Usage'}\n"
    report += "-" * 45 + "\n"

    report += (
        f"{server['name']:15}"
        f"₹{server['monthly_cost']:<14}"
        f"{server['avg_cpu_usage']}%\n"
    )

    report += (
        f"\nInsight: {server['name']} "
        f"is the most expensive server."
    )

    return report


def generate_shutdown_report(data):

    server = get_shutdown_candidate(data)

    if server is None:
        return "\nNo shutdown candidates found."

    report = "\n========== SHUTDOWN ANALYSIS ==========\n"
    report += f"{'Server':15}{'CPU Usage':15}{'Monthly Cost'}\n"
    report += "-" * 50 + "\n"

    report += (
        f"{server['name']:15}"
        f"{server['avg_cpu_usage']}%{'':10}"
        f"₹{server['monthly_cost']}\n"
    )

    report += (
        f"\nRecommendation: {server['name']} "
        f"has very low utilization and may be considered "
        f"for shutdown or consolidation."
    )

    return report


def generate_oldest_code_report(data):

    repo = get_oldest_repository(data)

    report = "\n========== OLDEST REPOSITORY ==========\n"
    report += (
        f"{'Repository':20}"
        f"{'Language':15}"
        f"{'Last Commit'}\n"
    )

    report += "-" * 60 + "\n"

    report += (
        f"{repo['name']:20}"
        f"{repo['language']:15}"
        f"{repo['last_commit_date']}\n"
    )

    report += (
        f"\nInsight: {repo['name']} "
        f"contains the oldest codebase."
    )

    return report


# =====================================
# NATURAL LANGUAGE QUERY ENGINE
# =====================================

def process_query(query, data):

    query = query.lower()

    cost_keywords = [
        "cost",
        "money",
        "expense",
        "waste",
        "spending",
        "खर्च",
        "पैसे",
        "वाया"
    ]

    shutdown_keywords = [
        "shutdown",
        "close",
        "remove",
        "stop",
        "terminate",
        "बंद",
        "काढू"
    ]

    old_code_keywords = [
        "old",
        "oldest",
        "legacy",
        "stale",
        "जुना",
        "पुराना"
    ]

    if any(word in query for word in cost_keywords):
        return generate_cost_report(data)

    elif any(word in query for word in shutdown_keywords):
        return generate_shutdown_report(data)

    elif any(word in query for word in old_code_keywords):
        return generate_oldest_code_report(data)

    return """
Query not recognized.

Example Queries:
- Where is the most money being spent?
- Which server can be shutdown?
- What is the oldest repository?
- सगळ्यात जास्त पैसे कुठे वाया जातायत?
- कोणता सर्व्हर बंद करू शकतो?
- सगळ्यात जुना कोड कोणता आहे?
"""


# =====================================
# MAIN PROGRAM
# =====================================

def main():

    print("=" * 60)
    print("NATURAL LANGUAGE IT ANALYSIS ENGINE")
    print("=" * 60)

    while True:

        query = input(
            "\nAsk a question (type 'exit' to quit):\n> "
        )

        if query.lower() == "exit":
            print("\nGoodbye!")
            break

        result = process_query(query, data)

        print(result)


if __name__ == "__main__":
    main()