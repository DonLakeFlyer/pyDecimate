* Takes airpy_rx output as stdin. So pipe airspy_rc to 'python pyDecimate'
* Does an 8 way FIR decimate
* Spits out results over udp://127.0.0.1:10000
* Log a warning if there is input buffer overflow
