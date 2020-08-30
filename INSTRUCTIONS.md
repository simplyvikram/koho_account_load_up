

## Instructions

A solution for the problem statement defined in [README.MD](./README.md)

This program solely relies on the python3 standard library. No external packages are needed. 

Command to run the program:
```bash
python processor.py --input_file input.txt --output_file output.txt
```
Where `input.txt` containing the various load instructions is read, processed and `output.txt` is produced.
If `output.txt` already exists, it is overwritten.


## Tests
Unit tests are provided in `test_processor.py`
Command to run tests:
```bash
python -m unittest test_processor.TestProcessor
```