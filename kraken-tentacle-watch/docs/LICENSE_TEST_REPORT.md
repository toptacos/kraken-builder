# Free vs premium license tests
Run at 2026-09-26T00:00:55.565195+00:00
## Official kraken-builder
```

tests/test_license.py::test_free_tentacle_does_not_need_key PASSED       [  6%]
tests/test_license.py::test_premium_without_key_fails PASSED             [ 13%]
tests/test_license.py::test_premium_with_local_key_offline PASSED        [ 20%]
tests/test_license.py::test_echo_still_runs PASSED                       [ 26%]
tests/test_license_cli.py::test_license_set_and_status PASSED            [ 33%]
tests/test_license_cli.py::test_verify_without_key PASSED                [ 40%]
tests/test_license_upgrade.py::test_upgrade_stores_key PASSED            [ 46%]
tests/test_license_upgrade.py::test_cli_upgrade PASSED                   [ 53%]
tests/test_license_upgrade.py::test_upgrade_fail PASSED                  [ 60%]
tests/test_billing_package.py::test_free_spec_is_not_premium PASSED      [ 66%]
tests/test_billing_package.py::test_after_install_hook_free PASSED       [ 73%]
tests/test_billing_package.py::test_denied_hook_logs PASSED              [ 80%]
tests/test_billing_package.py::test_client_set_and_status PASSED         [ 86%]
tests/test_billing_package.py::test_verify_without_key_raises PASSED     [ 93%]
tests/test_billing_package.py::test_billing_log_handler_ping PASSED      [100%]
```
## watch roles
```
test_free_assert_and_premium_overlay (__main__.WatchLicenseRoles.test_free_assert_and_premium_overlay) ... ok
test_manifest_is_free (__main__.WatchLicenseRoles.test_manifest_is_free) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.050s

OK
```
## marks roles
```
test_free_assert_and_premium_overlay (__main__.MarksLicenseRoles.test_free_assert_and_premium_overlay) ... ok
test_manifest_is_free (__main__.MarksLicenseRoles.test_manifest_is_free) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.149s

OK
```
## tentacle contracts (free arms)
### watch-contract.txt
```
test_unknown_action (__main__.WatchContract.test_unknown_action) ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.188s

OK
```
### marks-contract.txt
```
test_unknown_action (__main__.MarksContract.test_unknown_action) ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.912s

OK
```

All listed suites passed. watch and marks stay `license: free`.
