import yaml
import os
from data.generators.tickets import generate_tickets
from data.generators.services import generate_services
from data.generators.applications import generate_applications


def load_config(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    with open(path) as f:
        return yaml.safe_load(f)


def generate_all(config=None):
    if config is None:
        config = load_config()

    services_df, incidents_df, services_dq = generate_services(config)

    tickets_df, tickets_dq = generate_tickets(config, incidents_df)

    applications_df, applications_dq = generate_applications(config)

    all_quality_issues = {
        'tickets': tickets_dq,
        'services': services_dq,
        'applications': applications_dq,
    }

    return {
        'tickets': tickets_df,
        'services': services_df,
        'applications': applications_df,
        'incidents': incidents_df,
        'quality_issues': all_quality_issues,
        'config': config,
    }


if __name__ == '__main__':
    data = generate_all()
    for key in ['tickets', 'services', 'applications']:
        print(f"{key}: {len(data[key])} rows")
    print("\nData quality issues:")
    for source, issues in data['quality_issues'].items():
        for issue in issues:
            print(f"  [{source}] {issue}")
