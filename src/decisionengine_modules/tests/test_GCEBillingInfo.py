# SPDX-FileCopyrightText: 2017 Fermi Research Alliance, LLC
# SPDX-License-Identifier: Apache-2.0

import json

from unittest.mock import MagicMock, patch

import bill_calculator_hep.GCEBillAnalysis
import pandas
import pytest
import structlog

from google.auth.exceptions import RefreshError
from pandas.testing import assert_frame_equal

from decisionengine_modules.GCE.sources import GCEBillingInfo

# TODO
# The GCEBillingInfo module needs to be refactored so that tests
# can be written.  Then tests can be written to test smaller bits
# of code.  There is also an issue that the env has to have
# BOTO_CONFIG set, this has to be done outside of the code and
# can't be set in the test. Depending on how this testing is done
# you may be able to mock around this.

config_billing_info = {
    "channel_name": "GCETest",
    "projectId": "hc-de-test",
    "lastKnownBillDate": "10/01/18 00:00",  # '%m/%d/%y %H:%M'
    "balanceAtDate": 100.0,  # $
    "applyDiscount": True,  # DLT discount does not apply to credits
}


def test_produces():
    bi_pub = GCEBillingInfo.GCEBillingInfo(config_billing_info)
    assert bi_pub._produces == {"GCE_Billing_Info": pandas.DataFrame}


@pytest.fixture
def example_service_account_credential():
    return json.dumps(
        {
            "type": "service_account",
            "project_id": "hc-de-test",
            "private_key_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQD4499rviKPf+AR\nLuxv8vAjqi4RFAMJNQ0e5D0wkp9E1GcEW2PpXxoOF6RYBAfODkxsKD1jeVO0TusO\nY/P4YOfmnVwWl8dky7gn6JT49bOhGK17gLc3GM7mUKOiNZOowxz+c8XsiUUE1W4y\ncHioxfH09kf0AEZwXBqymrZGxJGTUM2Ksay7YCh75DbHkinjnvdelBJd7/3O1OtB\nnoj5hH7QIgqr7ntWmNgKzhgjIU72P/y5wix7Xv06J2vecJyRMd16p8PCj7W3TZQg\nAKZxugrn396buf74V60lHy9g/bVG6ppttLR5pqNz+YXyN77/j8ME+5DVLvqONA9N\nwF7khtrJAgMBAAECggEAeph4EVC/IlMZMi2cXgpa2h52AYiLdEoS8+/16gqW9Cbx\ntXY00Ru8sEtZ8tbNZ2SopS/vCSQWpH6pDtYSMvq8z94cIa7SkyY7yECqvLT+LbCD\np41/8d5A77ax23ErkhnFmtq5F+mHuzlMRgEblfqm04RKbfiCuc7MgcRuW45wrJBM\nd987fIPWLqIz0QiTiA7UjEWvT+HwXl0hEzVcepEbnXMqTMfIHh2GAok/hFxq+I9+\n+J5edmVuPnukuD10QfbdCKKKoXq1hEConBSCVMzLgJmNMCu5ZhOqnM3IiEFdvOvz\nSiWEMwqjWdCXdKRj7IlJ9/9Eyo9bHBHSXU5xxTJvBwKBgQD+os8A8lqOawWJLr4q\nDCSmu9lg8BqZFkSkqiwXrCuA7ZW00imLkJkKAs4xB+WNWmuQZrWz3B5s7MbG6s74\nT1+vDC8xoc1uc5+d0pNbTs7PqO+KeRe7oHp/yNUYHnzQCRyxprw5GTyng9+POl7r\nNnVBjjItp3/ieuBZVVtj9uXPSwKBgQD6OS9FNKUBiC5ipXxSeEKxAtN4bxKZ2ujS\nQZtPQRUz3p3U2ZMITW9IfE1tqGp9kkcvcnAYGuGqVX21AeN7ghtGPvzyu+U9Jk/+\nbNJhhmUQtHXlN50t4bDlrutbhuUJ4HjL291ITjAI5nZxrLXOjFglvZgJBl9iyGwm\n/7xDhUDtuwKBgCnacNPjAedux9YojLE0lcGiFrTMQlLvShEWt3Ccp/nlEzpJYPLD\nraPrmiCM/7ogJpXxi+QoRgf5UyLW7XX69es7wXYS9kU1VAMI3ZegeHXBer3z8Wax\nlfDy/bOdLz6ygLjigwWPlFykXFaabYeTx+oiiTTf1zFOqRmF4iOoLVXJAoGAP9ta\nIeo2dfagB9K9sHo6YtwaxbBq6dLA+e9+SDKOy6bzVn+UE1lXngMC64pAav1qp0Qo\nMS6jCoo4w3nQ6RMiDMJEYVnsPbfKUF7LLdJTdnjnYXDY7v2a3HLQY5JAX03m5fed\nODej8JGIBqiR2T1dvXvuEdeLfjUxzJ4VGJIoKMMCgYA4YhlmcZSnaq3GtaAxzkKo\nioo8yqwP0EJIQIZzIros05Z4j7iMIo9Bw0rLIoOB3Kq/g6CZ6oci71VoRsp4f76a\nvE44mvG0wCYath0p7sPIK8MY0aaOBHFeq6VeRYp1M73GnYNLRzwX7bLFeBiRkfAY\nYYSyYV7J7MUxIWwYyZ0BgQ==\n-----END PRIVATE KEY-----\n",
            "client_email": "gcloudbiller@hc-de-test.iam.gserviceaccount.com",
            "client_id": "123456789012345678901",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/gcloudbillerathepcloud-fnal.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
        }
    )


@pytest.fixture
def example_constants():
    return {
        "projectId": "hc-de-test",
        "lastKnownBillDate": "10/01/18 00:00",
        "balanceAtDate": 100.0,
        "applyDiscount": True,
    }


@pytest.fixture
def example_global_config():
    return {"graphite_host": "dummy", "graphite_context_billing": "dummy", "outputPath": "."}


# the following fixture, though not used, has been included to serve as an example for the structure of the cloud billing costs query result from BigQuery
@pytest.fixture
def example_cost_dataframe():
    return pandas.DataFrame(
        {
            "Sku": {0: "sku1", 1: "sku2", 2: "sku3", 3: "sku4", 4: "sku5"},
            "Service": {0: "service1", 1: "service1", 2: "service2", 3: "service2", 4: "service3"},
            "rawCost": {0: 1.344769, 1: 35.973946, 2: 1.5829, 3: 3.000000, 4: 328.35625},
            "rawCredits": {0: 2.0000, 1: 0.0000, 2: -1.0000, 3: 0.0000, 4: 2.0000},
        }
    )


@pytest.fixture
def expected_cost_subtotals():
    return {
        "service1.sku1": {"rawCost": 11.344769, "Credits": -2.0000, "Cost": 9.344769},
        "service1.sku2": {"rawCost": 35.973946, "Credits": 0.0000, "Cost": 35.973946},
        "service2.sku3": {"rawCost": 1.5829, "Credits": -1.0000, "Cost": 0.5829},
        "service2.sku4": {"rawCost": 3.000000, "Credits": 0.0000, "Cost": 3.000000},
        "service3.sku5": {"rawCost": 328.3562, "Credits": -6.0000, "Cost": 322.3562},
        "AdjustedSupport": 0.0,
        "Total": 371.257815,
    }


@pytest.fixture
def expected_adjustments_subtotals():
    return {"service1.sku2": 0.0, "service2.sku3": -0.000001, "service2.sku4": -0.000002, "Total": -0.000003}


@pytest.fixture
def expected_bill_summary():
    return pandas.DataFrame(
        {
            "service1.sku1": {0: {"rawCost": 11.344769, "Credits": -2.0000, "Cost": 9.344769}},
            "service1.sku2": {0: {"rawCost": 35.973946, "Credits": 0.0000, "Cost": 35.973946, "Adjustments": 0.0}},
            "service2.sku3": {0: {"rawCost": 1.5829, "Credits": -1.0000, "Cost": 0.5829, "Adjustments": -0.000001}},
            "service2.sku4": {0: {"rawCost": 3.000000, "Credits": 0.0000, "Cost": 3.000000, "Adjustments": -0.000002}},
            "service3.sku5": {0: {"rawCost": 328.3562, "Credits": -6.0000, "Cost": 322.3562}},
            "AdjustedSupport": {0: 0.0},
            "Total": {0: 371.257815},
            "AdjustedTotal": {0: 371.257815},
            "Balance": {0: -271.257815},
        }
    )


# the following unit test, when passed, verifies that the underlying dependency (bill-calculator-hep) for GCEBillingInfo module uses the version that involves the use of BigQuery
def test_gcebilling_dep_version(example_constants, example_global_config):
    calculator = bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator(
        None, example_global_config, example_constants, structlog.getLogger()
    )

    with pytest.raises(AttributeError) as e_msg:
        file_list = calculator._downloadBillFiles()
    assert str(e_msg.value) == "'GCEBillCalculator' object has no attribute '_downloadBillFiles'"


# the following unit tests specifically cater to the parts of GCEBilling that actually rely on BigQuery
# in the same test, have two fake credentials
# set different environment using monkeypatch and test for DefaultCredentialsError
def test_unable_to_auth_to_bqclient(
    tmp_path, example_service_account_credential, example_constants, example_global_config, monkeypatch
):
    print(tmp_path)
    d = tmp_path
    fake_creds = d / "fake_gce_cred.json"
    fake_creds.write_text(example_service_account_credential, encoding="utf-8")

    with monkeypatch.context() as m:
        m.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(fake_creds))

        calculator = bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator(
            None, example_global_config, example_constants, structlog.getLogger()
        )

        with pytest.raises(RefreshError) as e_msg:
            tst_billsummary = calculator.calculateBill()
        assert e_msg.value.args[1]["error_description"] == "Invalid grant: account not found"


def test_cost_subtotals(example_constants, example_global_config, expected_cost_subtotals, monkeypatch):
    def mock_costQueryData(self, bqc, tst_query, cost_query=True):
        mock_data = {
            "service1": {
                "sku1": {"rawCost": 11.344769, "rawCredits": -2.0000},
                "sku2": {"rawCost": 35.973946, "rawCredits": 0.0000},
            },
            "service2": {
                "sku3": {"rawCost": 1.5829, "rawCredits": -1.0000},
                "sku4": {"rawCost": 3.000000, "rawCredits": 0.0000},
            },
            "service3": {"sku5": {"rawCost": 328.3562, "rawCredits": -6.0000}},
        }
        return mock_data, "rawCost"

    monkeypatch.setattr(
        bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator, "queryCloudBillingData", mock_costQueryData
    )

    tst_calculator = bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator(
        None, example_global_config, example_constants, structlog.getLogger()
    )

    mock_bqclient = MagicMock()
    monkeypatch.setattr("google.cloud.bigquery.client.Client", mock_bqclient)
    dummy_query = "SELECT * FROM TABLE"
    cost_subtotals = tst_calculator.calculateSubTotals(mock_bqclient, dummy_query, cost_query=True)
    assert cost_subtotals == expected_cost_subtotals


def test_adjustments_subtotals(example_constants, example_global_config, expected_adjustments_subtotals, monkeypatch):
    def mock_adjQueryData(self, bqc, tst_query):
        mock_data = {
            "service1": {"sku2": {"rawAdjustments": 0.0, "rawCredits": 0.0}},
            "service2": {
                "sku3": {"rawAdjustments": -0.000001, "rawCredits": 0.0},
                "sku4": {"rawAdjustments": -0.000002, "rawCredits": 0.0},
            },
        }
        return mock_data, "rawAdjustments"

    monkeypatch.setattr(
        bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator, "queryCloudBillingData", mock_adjQueryData
    )

    tst_calculator = bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator(
        None, example_global_config, example_constants, structlog.getLogger()
    )

    mock_bqclient = MagicMock()
    monkeypatch.setattr("google.cloud.bigquery.client.Client", mock_bqclient)
    dummy_query = "SELECT * FROM TABLE"
    adjustments_subtotals = tst_calculator.calculateSubTotals(mock_bqclient, dummy_query)
    assert adjustments_subtotals == expected_adjustments_subtotals


def test_bill_calculation(
    example_constants,
    example_global_config,
    expected_cost_subtotals,
    expected_adjustments_subtotals,
    expected_bill_summary,
    monkeypatch,
):
    tst_calculator = bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator(
        None, example_global_config, example_constants, structlog.getLogger()
    )
    # mocking a BigQuery Client object...
    mock_bqclient = MagicMock()
    monkeypatch.setattr(bill_calculator_hep.GCEBillAnalysis.bigquery, "Client", mock_bqclient)

    # monkeypatching the two invocations of calculateSubTotals to directly return the results of the mocked version of the queryCloudBillingData()
    # the same method is called twice in the actual execution flow and returns different results depending on whether the cost_query flag is set. the mocked behavior is achieved using side effect as shown below.
    with patch.object(
        bill_calculator_hep.GCEBillAnalysis.GCEBillCalculator,
        "calculateSubTotals",
        side_effect=[expected_cost_subtotals, expected_adjustments_subtotals],
    ) as mock_method:
        tst_bill_summary = tst_calculator.calculateBill()
        assert_frame_equal(tst_bill_summary, expected_bill_summary)
