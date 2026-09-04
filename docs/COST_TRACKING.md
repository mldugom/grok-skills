# Grok cost tracking

`grok-cost` tracks observed Grok spend from the xAI prepaid balance shown in the billing UI.

It intentionally does **not** infer billing from:

- the Grok status-line `$` value,
- context tokens,
- turn count,
- tool-call count.

Those are useful efficiency diagnostics, but the balance delta is the authoritative observed account debit when no top-up, refund, credit, or other concurrent xAI usage occurs during the measurement window.

## Typical session

Before opening Grok, note the current xAI prepaid balance and run:

```bash
grok-cost start 20.00 --label "crypto A0"
```

At any point, enter the currently displayed balance:

```bash
grok-cost status 16.30
```

At session end:

```bash
grok-cost end 16.30
```

Recent sessions:

```bash
grok-cost history --limit 10
```

State is stored outside repositories under:

```text
~/.grok/cost-tracker/current.json
~/.grok/cost-tracker/sessions.csv
```

No API key or billing secret is stored.

## Interpretation

If a session begins at `$20.00` and ends at `$16.30`, observed spend is exactly `$3.70` for that measurement window.

This is only attributable to the tracked Grok session when there was no other xAI usage and no balance adjustment during the same window. If the ending balance is greater than the starting balance, the tracker refuses to call the delta session spend because a top-up/credit or wrong balance entry likely occurred.

The built-in Grok status-line `cost` item should be treated as a session/runtime diagnostic, not as a replacement for prepaid-balance reconciliation.
