from random import choice, randint, random, sample
import yaml

def generate_varied_yaml(index):
    options = [
        lambda i: {
            "user": {
                "id": i,
                "name": f"user_{i}",
                "active": i % 2 == 0,
                "roles": ["admin", "editor", "viewer"][:i % 4]
            }
        },
        lambda i: {
            "settings": {
                "theme": choice(["dark", "light"]),
                "volume": randint(0, 100),
                "features": {
                    "beta": bool(i % 3),
                    "release": True
                }
            }
        },
        lambda i: {
            "servers": [
                {"host": f"server{i}.local", "port": 8000 + i},
                {"host": f"backup{i}.local", "port": 9000 + i}
            ]
        },
        lambda i: {
            "pipeline": {
                "steps": [
                    {"name": "extract", "enabled": True},
                    {"name": "transform", "enabled": bool(i % 2)},
                    {"name": "load", "enabled": True}
                ]
            }
        },
        lambda i: {
            "metrics": {
                "latency": round(random() * 100, 2),
                "throughput": randint(100, 1000),
                "errors": None if i % 4 else 0
            }
        },
        lambda i: {
            f"task_{i}": {
                "description": f"This is task {i}",
                "tags": [f"tag{i}", f"priority{i%3}"],
                "dependencies": [f"task_{j}" for j in range(i-2, i) if j > 0]
            }
        },
        lambda i: {
            "matrix": {
                "row1": [i, i+1, i+2],
                "row2": [i+3, i+4, i+5]
            }
        },
        lambda i: {
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {
                            "value": f"deep_{i}"
                        }
                    }
                }
            }
        },
        lambda i: {
            "log": {
                "timestamp": f"2024-01-{i % 30 + 1:02d}T12:00:00Z",
                "message": f"Log entry {i}",
                "level": choice(["INFO", "WARN", "ERROR"])
            }
        },
        lambda i: {
            "config": {
                "enable_cache": bool(i % 2),
                "paths": {
                    "input": f"/data/input/{i}",
                    "output": f"/data/output/{i}"
                }
            }
        },
        lambda i: {
            "user": {
                "id": i,
                "name": f"user_{i}",
                "address": {
                    "street": f"{i} Main St.",
                    "city": "Sample City",
                    "zipcode": f"12345-{i}"
                },
                "preferences": {
                    "newsletter": bool(i % 2),
                    "dark_mode": bool(i % 3),
                    "notifications": ["email", "sms"][:i % 2]
                }
            }
        },
        lambda i: {
            "product": {
                "id": i,
                "name": f"product_{i}",
                "variants": [
                    {"color": "red", "size": "M"},
                    {"color": "blue", "size": "L"}
                ],
                "reviews": [
                    {"user": f"user_{i+1}", "rating": randint(1, 5), "comment": f"Great product! {i}"},
                    {"user": f"user_{i+2}", "rating": randint(1, 5), "comment": f"Not bad. {i}"}
                ]
            }
        },
        lambda i: {
            "categories": {
                f"category_{i}": {
                    "name": f"Category {i}",
                    "subcategories": [
                        {"name": f"Subcategory {j}", "id": j} for j in range(1, 4)
                    ]
                }
            }
        },
        lambda i: {
            "profile": {
                "username": f"user_{i}",
                "followers": randint(100, 10000),
                "posts": [
                    {"id": f"post_{i+1}", "content": f"Post content {i+1}", "likes": randint(0, 100)},
                    {"id": f"post_{i+2}", "content": f"Post content {i+2}", "likes": randint(0, 100)}
                ]
            }
        },
        lambda i: {
            "server": {
                "hostname": f"server_{i}",
                "status": choice(["active", "inactive"]),
                "config": {
                    "cpu": f"Intel {randint(1, 5)} GHz",
                    "ram": f"{randint(4, 32)} GB",
                    "storage": f"{randint(100, 2000)} GB",
                    "network": {
                        "ip": f"192.168.1.{i}",
                        "subnet": "255.255.255.0",
                        "gateway": "192.168.1.1"
                    }
                }
            }
        },
        lambda i: {
            "event": {
                "id": i,
                "timestamp": f"2024-05-{i%30 + 1:02d}T12:00:00Z",
                "type": choice(["INFO", "WARN", "ERROR"]),
                "source": f"source_{i}",
                "metadata": {
                    "level": randint(1, 5),
                    "details": f"Additional information about event {i}",
                    "user": f"user_{i+1}"
                }
            }
        },
        lambda i: {
            "weather": {
                "city": f"city_{i}",
                "date": f"2024-05-{i%30 + 1:02d}",
                "forecast": {
                    "temperature": round(random() * 40, 2),
                    "humidity": randint(20, 100),
                    "conditions": choice(["clear", "rain", "cloudy", "snow"]),
                },
                "historical": {
                    "high": randint(20, 35),
                    "low": randint(5, 20)
                }
            }
        },
        lambda i: {
            "schedule": {
                "day": f"2024-05-{i%30 + 1:02d}",
                "events": [
                    {"start": f"09:00", "end": f"11:00", "title": f"Event {i}"},
                    {"start": f"12:00", "end": f"14:00", "title": f"Meeting {i}"}
                ]
            }
        },
        lambda i: {
            "employee": {
                "id": i,
                "name": f"Employee {i}",
                "department": choice(["HR", "Engineering", "Sales"]),
                "performance": {
                    "review_score": randint(1, 5),
                    "comments": f"Performance comments for employee {i}",
                    "goals": [f"Goal {i} for employee"]
                }
            }
        },
        lambda i: {
            "response": {
                "status": choice(["success", "error"]),
                "data": {
                    "id": i,
                    "type": choice(["product", "order", "user"]),
                    "attributes": {
                        "name": f"Name_{i}",
                        "description": f"Description of {i}"
                    }
                },
                "message": f"Operation {i} completed"
            }
        },
    lambda i: {
            "data": [
                {"id": i, "value": choice([True, False, None, randint(0, 100)])},
                {"id": i+1, "value": choice([True, False, None, randint(0, 100)])}
            ]
        }
    ]
    
    chosen_generators = sample(options, k=randint(1, 8))
    combined_result = {}

    for gen in chosen_generators:
        part = gen(index)
        combined_result.update(part)
    return combined_result

def gen_data(dirName, ndocs = 151):
    for i in range(ndocs):
        content = generate_varied_yaml(i)
        yaml_content = yaml.dump(content, sort_keys=False)
        filename = f"{i:02d}_varied.yaml"
        with open(f"{dirName}/{filename}", "w", encoding="utf-8") as f:
            f.write(yaml_content)

