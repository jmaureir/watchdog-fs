Name:           watchdog-fs
Version:        0.5
Release:        1%{?dist}
Summary:        A simple filesystem event capturer triggering (delayed)actions
License:        MIT
URL:            https://github.com/jmaureir/watchdog-fs
Source0:        %{name}-%{version}.tar.gz

Requires:       python3, python3-pip

%description
Simple filesystem event capturer for triggering (delayed) actions (python functions) configured as script files

%global debug_package %{nil}

%prep
%autosetup

%build
%install
mkdir -p $RPM_BUILD_ROOT/usr/sbin
mkdir -p $RPM_BUILD_ROOT/etc/watchdog-fs/actions.d
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig

cp watchdog-fs.py $RPM_BUILD_ROOT/usr/sbin
cp -rf etc/*.ini $RPM_BUILD_ROOT/etc/watchdog-fs
cp -rf actions.d/* $RPM_BUILD_ROOT/etc/watchdog-fs/actions.d
cp -rf etc/systemd/watchdog-fs.service $RPM_BUILD_ROOT/etc/systemd/system
cp -rf etc/sysconfig/watchdog-fs $RPM_BUILD_ROOT/etc/sysconfig

%pre
echo "installing dependencies: watchdog"
pip3 install -q watchdog

%post
systemctl daemon-reload

%files
%defattr(-,root,root,-)
/usr/sbin/watchdog-fs.py
/etc/watchdog-fs/watchdog-fs.ini
/etc/systemd/system/watchdog-fs.service
/etc/sysconfig/watchdog-fs
/etc/watchdog-fs/actions.d/log.py
/etc/watchdog-fs/actions.d/mv.py

%changelog
* Fri May 03 2025 jcm <jmaureir at gmail.com> - 0.5-1
- Initial package build
