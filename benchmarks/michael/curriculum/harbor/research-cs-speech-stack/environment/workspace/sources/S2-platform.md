# S2 — Development and target platform note

Development happens on an x64 desktop. The target is an ARM64 laptop
(Windows 11 on ARM). An NPU is present on the target but is optional.

> Model output quality is deterministic across CPU architectures. Only speed
> differs.

Every error rate and DER measured on the x64 desktop (S4, S5) therefore applies
unchanged on the ARM64 target.

Speed is different: x64 real-time factors (S4 column `x64_rtf`) say nothing
about ARM64 throughput. No ARM64 timing has been measured yet — that needs the
physical target device, which is not available to the project at the time of
this note.
