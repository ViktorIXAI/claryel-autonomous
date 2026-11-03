# Tesla P100 GPU-mode switch: compute (16 GB BAR1) -> graphics (256 MB BAR1)

Date: 2026-11-03. Host used for the switch: P1005 (card temporarily installed
there and fully working). Target machine for the card: P3032 (HP Z220).

## Why

P3032 (HP Z220, C226, BIOS K51 v01.87) failed to initialize the P100 with:

```text
NVRM: This PCI I/O region assigned to your NVIDIA device is invalid:
NVRM: BAR1 is 0M @ 0x0 (PCI:0000:01:00.0)
```

Diagnosis (measured on P3032):

* e820/iomem: RAM tops out at 0xDFFFFFFF, `TOLM=0xE0000000` (lock bit set) ->
  a 512 MB 32-bit MMIO hole at 0xE0000000-0xEFFFFFFF.
* Root-port (00:01.0) 64-bit prefetch window registers read 0 and ignore
  writes (locked at zero): no above-4G aperture, no BIOS option for it.
* Card BAR1 size mask = 16 GiB class; no Resizable BAR capability present.
* A 16 GiB BAR cannot fit into a 512 MB sub-4G window -> probe fails.

The P100 firmware stores a persistent "GPU mode": Compute (default,
BAR1 = full 16 GB) or Graphics (BAR1 = 256 MB, PCI class VGA-compatible).
256 MB fits the Z220 hole exactly. Switching requires a machine where the
card initializes; P1005 is such a machine.

## What was done (P1005, nvflash 5.867 linux, MD5 of zip matched vendor record)

1. Strata serve stopped, keep-up cron paused (restored afterwards),
   nvidia-persistenced stopped, `nvidia*` modules unloaded.
2. Firmware backup: `nvflash --save p100_original.rom`
   272,896 bytes, sha256 `c9c09173b69a0082c177e907abebd49a1068d8202c433e32e5160b2ddaf0fe00`
   (kept in the private local evidence bundle; vendor firmware blob not
   committed to the public repo).
3. `nvflash --protectoff`
4. `nvflash --gpumode graphics` ->
   `Successfully updated GPU mode to "physical_display_enabled_256MB_bar1" ( Mode 1 )`
5. `nvidia-smi -e 1` (ECC re-enabled; mode flash turns ECC off).
6. Full power-off, cold boot via Wake-on-LAN, re-verified.

## Before / after (measured)

| item | before (compute) | after (graphics) |
|---|---|---|
| PCI class | 3D controller | VGA compatible controller |
| BAR1 | 16 GiB @ 0x3b800000000 | 256 MiB @ 0xe0000000 |
| nvidia-smi BAR1 total | 16384 MiB | 256 MiB |
| ECC | enabled | enabled (re-armed, verified current) |
| driver | 580.196.07 loads | 580.196.07 loads |

BAR1 landed at 0xe0000000 on P1005 — the same address class that is free on
P3032. Expected effect on P3032: driver probe succeeds; then apply 150 W
power limit immediately (PSU/cable constraint documented in P3032 records).

## Failures on record

* nvflash refuses flash while `nvidia*` modules loaded; between unload and
  flash the modules were reloaded twice by concurrent host monitoring
  (keep-up/`nvidia-smi` pollers). Fix: temporary modprobe blacklist
  `/etc/modprobe.d/z99-flash-temp.conf` during the operation, removed after.
* nvflash confirmation prompts read from the keyboard: piping `y` failed
  ("console read: Bad file descriptor"). Fix: allocate a pty (`ssh -tt`) and
  feed two `y` answers (two separate prompts).
* `apt install acpi-call-dkms` on P3032 earlier died with gcc-13 internal
  compiler error — unrelated to the flash, documented for P3032 fan work.

## Reversibility

`nvflash --gpumode compute` restores the original state; the saved ROM
backup covers recovery. Mode lives in card EEPROM, read at power-on, so a
full power cycle is mandatory after any mode change.
