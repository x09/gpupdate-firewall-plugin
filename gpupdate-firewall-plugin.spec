%define _unpackaged_files_terminate_build 1
%define _destdir %_datadir/PolicyDefinitions

Name: gpupdate-firewall-plugin
Version: 1.0
Release: alt1

Summary: Firewall (iptables) management plugin for gpupdate
License: GPLv3+
Group: System/Configuration/Other
Url: https://github.com/altlinux/gpupdate-plugin-x09-firewall
BuildArch: noarch
AutoReqProv: no

BuildRequires(pre): rpm-build-python3
BuildRequires: gettext-tools
BuildRequires: python3-module-pytest

Requires: iptables
Requires: gpupdate >= 0.16

Source0: %name-v%version.tgz

%description
Firewall management policy plugin for gpupdate. Reads firewall rules
from GPO settings and applies them to iptables using dedicated managed
chains (FW_PLUGIN_INPUT / FW_PLUGIN_OUTPUT), without touching other
rules. The ruleset is persisted for reboot survival.

%package -n admx-x09-firewall
Summary: x09 Firewall management ADMX policy templates
License: AGPLv3+
Group: System/Configuration/Other

%description -n admx-x09-firewall
x09 ADMX templates for managing firewall rules via iptables.
Provides a policy to define a list of firewall rules (direction,
protocol, port, source, destination, action).

%prep
%setup -q -n %name-v%version 

%install
mkdir -p %buildroot/usr/lib/gpoa/plugins
install -m0644 plugin/x09_firewall.py \
    %buildroot/usr/lib/gpoa/plugins/x09_firewall.py

mkdir -p %buildroot/usr/lib/gpoa/plugins/locale/ru_RU/LC_MESSAGES
msgfmt -o %buildroot/usr/lib/gpoa/plugins/locale/ru_RU/LC_MESSAGES/x09_firewall.mo \
    locale/ru_RU/LC_MESSAGES/x09_firewall.po

mkdir -p %buildroot/usr/lib/gpoa/plugins/locale/en_US/LC_MESSAGES
msgfmt -o %buildroot/usr/lib/gpoa/plugins/locale/en_US/LC_MESSAGES/x09_firewall.mo \
    locale/en_US/LC_MESSAGES/x09_firewall.po

mkdir -p %buildroot%_destdir
cp -r admx/ru-RU/ admx/en-US/ admx/*.admx %buildroot%_destdir/

%check
%__python3 -m pytest -vra tests/

%files
/usr/lib/gpoa/plugins/x09_firewall.py*
/usr/lib/gpoa/plugins/locale

%files -n admx-x09-firewall
%doc README_plugin.md README_plugin_en.md 
%dir %_destdir
%_destdir

%changelog
* Mon Aug 17 2026 Anton Shevtsov <shevtsov.anton@gmail.com> 1.0-alt1
- Initial release
