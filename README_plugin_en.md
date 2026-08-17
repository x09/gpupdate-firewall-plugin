# x09_firewall Plugin for gpupdate

This plugin extends the gpupdate (GPOA) group policy system on ALT OS with
the ability to centrally manage the firewall (iptables) through domain group
policies.

Rules are defined using the "Firewall Rules Management" ADMX template and
applied on client machines each time `gpupdate` runs.

## How It Works

1. An administrator fills in a list of rules in the Group Policy Editor
   (ADMX policy `FirewallRulesList`). Each rule is one line in the list.
2. Rules are saved to SYSVOL and placed in the client registry at
   `Software/Policies/x09/Firewall` as values `Rule1`, `Rule2`, etc.
3. When `gpupdate` runs, the plugin manager invokes this plugin in machine
   context (with root privileges).
4. The plugin reads the rules, translates them into iptables rules, and
   applies them to dedicated custom chains.

## Rule Format

Each rule is a single line in "key=value" format, with fields separated by `;`:

```
Action=Allow;Direction=In;Protocol=TCP;Port=80;Source=10.0.0.0/24;Destination=192.168.1.1
```

Field names and order are case-insensitive.

| Field         | Required | Values                                                      |
|---------------|----------|-------------------------------------------------------------|
| `Action`      | yes      | `Allow`, `Deny`, `Reject`                                   |
| `Direction`   | yes      | `In` (incoming), `Out` (outgoing)                           |
| `Protocol`    | yes      | `TCP`, `UDP`                                                |
| `Port`        | no       | single port (`80`), range (`53-153`), or list (`22,80,443`)|
| `Source`      | no       | IP address or CIDR network                                  |
| `Destination` | no       | IP address or CIDR network                                  |

**Notes:**
- Action translation: `Allow → ACCEPT`, `Deny → DROP`, `Reject → REJECT`.
- The `Port` field can contain:
  - single port: `Port=80` → `--dport 80`
  - port range: `Port=53-153` → `-m multiport --dports 53-153`
  - port list: `Port=22,80,443` → `-m multiport --dports 22,80,443`
- When using ranges and lists, the iptables `multiport` module is automatically applied.

Invalid rules are skipped with a warning logged; processing of remaining rules
continues.

## iptables Application Model

The plugin does not directly modify the system `INPUT`/`OUTPUT` chains, but
works through its own chains:

- `FW_PLUGIN_INPUT` — for rules with `Direction=In`;
- `FW_PLUGIN_OUTPUT` — for rules with `Direction=Out`.

On each run:

1. Custom chains are created if absent, and a jump rule (`-j`) is added as the
   first rule in the system `INPUT`/`OUTPUT` chains (idempotent).
2. The contents of **only** the custom chains are flushed (`-F`) and
   repopulated from the policy.

This approach:

- does not affect other firewall rules on the machine;
- does not block traffic by default — at the end of our chains an implicit
  return (`RETURN`) to the system chain occurs, so access (e.g., via SSH) is
  not interrupted even if the policy is empty.

## Persistence

After applying rules, the plugin saves the current rule set using
`iptables-save` to the file `/etc/sysconfig/iptables` (standard ALT mechanism)
so that rules persist after reboot. The path is defined by the
`IPTABLES_SAVE_PATH` constant in the plugin code.

## Current Limitations

- Only classic `iptables` (IPv4) is supported, `INPUT`/`OUTPUT` chains.
- IPv6 (`ip6tables`) and the `nftables` backend are not supported.
- Port is applied as destination port (`--dport`) for both directions.
- Port ranges and lists require the kernel `multiport` module (loaded by default in most systems).

## Installation

### Manual method

#### Installing ADMX templates

On the domain controller, place the admx/adml files in `/usr/share/PolicyDefinitions`:

```
/usr/share/PolicyDefinitions/x09-Firewall.admx
/usr/share/PolicyDefinitions/{ru-RU,en-US}/x09-Firewall.adml
```

Then load them into SysVol with the command:

```
samba-tool gpo admxload -UAdministrator
```

#### Installing the plugin on the client

The plugin is installed as a **flat file** in `/usr/lib/gpoa/plugins/` (no
subdirectory), translations in the shared `locale/` directory alongside the
plugin. The `/usr/lib/gpoa/` directory is provided by the `gpoa-lib` package —
no need to create it manually.

```
/usr/lib/gpoa/plugins/x09_firewall.py
/usr/lib/gpoa/plugins/locale/ru_RU/LC_MESSAGES/x09_firewall.mo
/usr/lib/gpoa/plugins/locale/en_US/LC_MESSAGES/x09_firewall.mo
```

### Automatic method

Install the RPM packages:

- `admx-x09-firewall` — package with ADMX templates (on the domain controller)
- `gpupdate-firewall-plugin` — package with the plugin (on the client)

## Localization

Log messages are translated into Russian and English (GNU gettext, domain
`x09_firewall`). The displayed language is determined by the system locale.

Rebuild translations after modifying `.po` files:

```bash
msgfmt locale/ru_RU/LC_MESSAGES/x09_firewall.po -o locale/ru_RU/LC_MESSAGES/x09_firewall.mo
msgfmt locale/en_US/LC_MESSAGES/x09_firewall.po -o locale/en_US/LC_MESSAGES/x09_firewall.mo
```
