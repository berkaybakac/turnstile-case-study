# Design decisions

[← Back to the overview](../README.md)

The production source is private. This repository holds the case study, its diagrams and aggregate charts. It contains no production code, customer or venue names, or partner data.

## Scope

**The platform authorizes individual member access.**
Accounts, packages, membership rules and the member app belong to the partner platform. The agent handles the connection, QR, screen, controller output and offline policy. Staff can request free mode locally.
- *Cost:* every new business rule waits for the platform; the device cannot "fix" a wrong decision locally.
- I ruled out caching membership data on unattended hardware. A local membership cache could diverge from the platform and would store personal data on site.

## Protocol

**Raw messages stop at one adapter.**
The adapter handles optional fields and resolves entry or exit from a grant before the runtime can request a pulse. An unresolved direction cannot trigger a pulse. Where an expected device identity is configured, state-changing events wait until it matches.
- *Cost:* each new field or action is a deliberate change in the adapter and the protocol notes, with tests.
- *Rejected:* passing payload dictionaries through the system. The platform's messages changed over time (aliases, optional fields, unexpected values); a tolerant reader at the edge keeps that variability away from hardware.

**Application-level credential checks.**
The platform can accept a WebSocket handshake before rejecting a credential. If the platform rejects the credential or expected device identity before the first successful application exchange in this run, the agent requests technician setup. After prior success, a later rejection follows the offline policy.

**The device detects dead connections itself.**
A keepalive ping with a short pong timeout closes a socket that still looks open but no longer carries traffic. The logs classify common connection failures and preserve an unknown category for investigation.
- *Rejected:* waiting for the operating system to report a broken socket, which can take far longer than members will wait at a turnstile.

## Availability

**Free passage during a sustained disconnect.**
The June field build switched to free passage after a sustained disconnect. In October I kept the member-facing message and added an “offline mode” label so staff could distinguish an outage from deliberate free passage. A stable reconnection clears the offline request. An independent staff or platform request can keep free mode active.

During a long outage the gates stay in offline free-pass. The venue accepts unchecked access during that interval. The grace period is configurable.

**Handling grants during an active pulse.**
The output pulse runs off the event loop, so QR refresh and new messages continue while a relay is held. Queuing a grant could trigger a pulse after its approval was relevant. A same-direction grant can extend the active pulse. The agent logs and ignores an opposing grant.

## Hardware

**One output port, several turnstile types.**
The runtime talks to a small output interface with a fake implementation (live smoke tests without driving hardware), GPIO implementations (a three-channel relay board and a single shared-pin variant) and a serial implementation for controllers driven over RS-485.
- *Safety:* the GPIO active level is validated against the device's hardware profile; a mismatch blocks the service from starting, because a wrong level would hold a relay energised.
- *Evidence boundary:* a completed serial write is not proof that a gate opened. Software support and physical acceptance are tracked separately.

**A card reader is another way to ask, not a key.**
A USB card reader's code is validated and sent to the platform on the current authenticated connection. It never drives the output directly; the platform decides as it does for a QR scan.

## Releases and the device

**No repository credentials on field devices.**
Runtime credentials are provisioned separately from the release bundle. The operator machine transfers an exact-tag Git bundle over SSH. Deployment checks the tag’s commit and verifies the bundle locally, checks its SHA-256 and verifies the bundle again on the Pi, then compares the checked-out commit with the expected hash.
- *Rejected:* pulling a branch on the device, which leaves a field device's version ambiguous and puts a long-lived secret on hardware in a public building.

**Candidate environments and a known-good rollback.**
Deploy reuses a healthy matching environment or prepares a hash-pinned candidate. Runtime and display checks precede activation. A failed candidate check can leave the live environment untouched. After restart, deploy verifies the service and attempts recovery if verification fails. The operator can redeploy a known-good tag. System package updates are a separate maintenance step.
- Preparing a candidate uses extra disk on the Pi, and activating it requires a service restart.

**A native user service, not a container.**
The kiosk needs the graphical session, the browser and GPIO devices on the host. A systemd user service in the kiosk session with a locked Python environment is simpler and more predictable on a Raspberry Pi 3 than containerising around them.

**Bounded privilege for deployment.**
Routine deployment has two bounded passwordless root helpers. Each is root-owned and has an exact sudo rule.

## Display

**A local web kiosk in Chromium.**
The React kiosk streams state changes, polls during reconnection and clears stale member details after a grace period. The classic and portrait layouts poll for state. Motion on the portrait layout is opt-in.
- *Cost:* a dependency on Chromium and on the desktop session being ready at boot, which the runtime retries around.

**Fitting kiosk animation to the Pi’s thermal budget.**
On one Pi 3 B+, Chromium used 0.9–1.7 CPU cores with smooth animation timing and 0.15–0.35 with stepped timing. Only the smooth run crossed the soft-temperature limit during the ten-minute comparison.

**Device-local styling on a shared release.**
The gallery shows seven venue designs rendered with a demo QR and placeholder branding. A device-local stylesheet can change the appearance without modifying the shared release.
- *Cost:* each design must be checked on its own screen size and orientation; a screenshot from the real device is the acceptance test, because it catches what browser emulation can miss.

**Staff free mode with the customer's own PIN.**
On touch screens, staff can open the turnstile for a set time. The first tap asks the venue to choose its own PIN; it is stored only as a salted hash on the device, checked on every request and locked after repeated failures. A reset by the operator clears it and reopens first setup. Staff free mode is tracked separately from platform and offline free mode, so ending one never overrides the other.

## Fleet operations

**Outbound fleet telemetry.**
Each device pushes a heartbeat every minute and sends its audit log to the collector. Fleet telemetry requires no inbound monitoring port at the venue.

**Deduplicating retried batches.**
The collector remembers the last 2,048 record digests per device, so a retried batch can be acknowledged without counting its recent records twice.

**Device paging and fleet-wide signals.**
I arm device paging after activation and burn-in, using observed or known venue hours. Pending devices do not start those pages. Closing time alone does not clear a firing device alarm. QR and service rules require fresh heartbeats even while firing. If telemetry stops, either signal can end before recovery is confirmed.

Fleet and collector alerts have separate rules. Four or more devices entering offline free-pass within ten minutes signal a shared interruption for investigation. The correlation rule filters stale offline events. Alternating boots under one device identity raise a separate informational alert.

**Logs that carry metadata, not people.**
Logs record event names, lengths, hashes, validity flags and connection and message identifiers, never raw QR text, credentials, names, photos or card codes. That makes fleet-wide analysis possible without storing names, QR text or card codes in clear; the hashes are short and one-way, and only metadata is kept.
