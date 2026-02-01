import os
import sqlite3
import pytest
import asyncio
import shutil
from pathlib import Path
from examples.custom_tool_example import (
    DataAnalystAgent
)
from spoon_ai.chat import ChatBot
from spoon_ai.agents.base import AgentState
from asserts import AgentTestAssertions


# FIXTURE: Create test data (CSV file & SQLite database)
@pytest.fixture(scope="module")
def setup_data():
    """Setup test environment: Create a sample CSV file and SQLite database."""
    sample_data = """id,name,age,city,salary
    1,John Smith,34,New York,75000
    2,Mary Johnson,28,San Francisco,85000
    3,Robert Brown,45,Chicago,92000
    4,Patricia Davis,31,Boston,78000
    5,James Wilson,39,Seattle,88000
    6,Jennifer Moore,27,Austin,72000
    7,Michael Taylor,42,Denver,95000
    8,Elizabeth Anderson,36,Portland,82000
    9,David Thomas,29,Los Angeles,79000
    10,Susan Jackson,44,Miami,91000
    """
    
    os.makedirs("tests/data", exist_ok=True)
    csv_path = "tests/data/employees.csv"

    # Create a CSV file
    with open(csv_path, "w") as f:
        f.write(sample_data)
    
    # Create a SQLite Database
    db_path = "tests/data/sample.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        city TEXT,
        salary INTEGER
    )
    """)
    
    # Insert data
    conn.execute("DELETE FROM employees")  # Clear the database
    conn.executemany(
        "INSERT INTO employees (id, name, age, city, salary) VALUES (?, ?, ?, ?, ?)",
        [
            (1, "John Smith", 34, "New York", 75000),
            (2, "Mary Johnson", 28, "San Francisco", 85000),
            (3, "Robert Brown", 45, "Chicago", 92000),
            (4, "Patricia Davis", 31, "Boston", 78000),
            (5, "James Wilson", 39, "Seattle", 88000),
        ]
    )
    conn.commit()
    conn.close()

    return csv_path, db_path

# FIXTURE: Create Agent and reset it after each test
@pytest.fixture
async def agent():
    """Fixture to create an agent and ensure it resets state after each test."""
    # Try to use new LLM manager architecture first, fallback to legacy if needed
    try:
        a = DataAnalystAgent(llm=ChatBot(use_llm_manager=True))
        print("✓ Using new LLM manager architecture for tests")
    except Exception as e:
        print(f"⚠ Falling back to legacy mode for tests: {e}")
        a = DataAnalystAgent(llm=ChatBot(use_llm_manager=False))
        print("✓ Using legacy ChatBot architecture for tests")
    
    yield a  # Pass `agent` to the test function
    a.clear()  # Clear state after test
    a.state = AgentState.IDLE  # Reset agent state
    print(f"Agent state reset after test: {a.state}")


# # TEST: Test DataAnalystAgent to process CSV and database queries
@pytest.mark.asyncio
@pytest.mark.parametrize("query_template, expected_snippet, special_check", [
    (
        "Analyze the {csv_path} file and give me a summary",
        "The dataset contains information about employees",
        False
    ),
    (
        "What are the average salaries in the database {db_path}?",
        "average salary",
        False
    ),
    (
        "Read the first 5 rows of the {csv_path} file",
        ["john smith", "patricia davis"],
        True
    ),
    (
        "How many employees are in each city according to the {csv_path} file?",
        "employee",
        False
    )
])
async def test_data_analyst_agent(query_template, expected_snippet, special_check, setup_data, agent):
    """Test DataAnalystAgent's ability to process CSV and database queries via parametrize."""

    csv_path, db_path = setup_data
    query = query_template.format(csv_path=csv_path, db_path=db_path)

    print(f"Running query: {query}")
    response = await agent.run(query)
    print(f"Response:{response}")

    if special_check:
        # For row data checks
        for keyword in expected_snippet:
            assert keyword in response.lower()
    else:
        assert expected_snippet.lower() in response.lower()

    print(f"Agent state reset after query: {query}")


@pytest.mark.asyncio
@pytest.mark.parametrize("query, expected",[
    (
        "Get the latest price of neo from neo mainnet",
        "The latest price of Neo"
    ),
    (
        "Get the latest block number from the neo mainnet",
        "The latest block number on the Neo mainnet"
    ),
    (
        "Use the api_request tool to make a POST request to https://neoxt4seed2.ngd.network "
        "with headers={'Content-Type': 'application/json'} "
        "and data={'jsonrpc': '2.0', 'method': 'eth_getBalance', 'params': ['0xd7e0E170d285Ec91460CB5Cd49668523c8571065','latest'], 'id': 1}",
        "'jsonrpc': '2.0'"
    )

])
async def test_api_request_agent(agent,query,expected):
    """
    Test APIRequestTool to verify it correctly processes queries and executes API requests.
    
    This test covers:
    1. Fetching NEO price from neo mainnet
    2. Retrieving the latest block number from Neo mainnet
    3. Sending a POST request to a test API
    4. Fetching balances from the NeoX testnet RPC API
    """

    print(f"=== Running Query: {query} ===")
    
    # Execute the agent query
    response = await agent.run(query)

    print(f"Response:{response}")
    AgentTestAssertions.assert_keywords_in_response(response,query,expected)


test_dir = Path("tests/data")
@pytest.mark.asyncio
@pytest.mark.parametrize("query, expected", [
    ("Write 'Hello, AI!' to a file at path 'tests/data/hello.txt'", "Successfully wrote"),
    ("Read the content of the file at path 'tests/data/hello.txt'", "Hello, AI!"),
    ("List all files in the directory tests/data", "Contents of directory"),
    ("Read the file at 'tests/data/missing_file.txt'", ["Error: File", "does not exist"]),
    ("List files in the directory 'non_existent_dir'", ["Error: Path", "does not exist"]),
])
async def test_filesystem_agent(query, expected, agent):
    """
    Parametrized test for FileSystemTool via AI agent interaction.
    Covers:
    1. Writing
    2. Reading
    3. Listing
    4. Error handling
    """

    # Prepare test directory if needed
    if not test_dir.exists():
        test_dir.mkdir(parents=True)

    print(f"=== Running Query: {query} ===")
    try:
        response = await agent.run(query)
        print(f"Response:{response}")

        assert response is not None, f"Query `{query}` returned None!"
        assert isinstance(response, str), f"Query `{query}` returned non-string: {response}"

        if isinstance(expected, list):
            assert any(e.lower() in response.lower() for e in expected), \
                f"Expected one of `{expected}` in response `{response}`"
        else:
            assert expected.lower() in response.lower(), \
                f"Expected `{expected}` in response `{response}`"

    except Exception as e:
        pytest.fail(f"Test failed on query `{query}` due to exception: {e}")


@pytest.fixture(scope="session", autouse=True)
def cleanup_files():
    yield
    try:
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("Test files cleaned up.")
    except Exception as e:
        print(f"Cleanup failed: {e}")
