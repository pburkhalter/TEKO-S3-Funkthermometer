from pprint import pprint
from piscope.decoder import Decoder


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("This is a simple decoder for raw piscope data captured from a 433Mhz-Thermometer")
    # filepath = input("Please enter the filepath for the raw data: ")
    filepath = "raw_dump"

    raw_decoder = Decoder()
    result = raw_decoder.decode(filepath)

    print("Decoded result:")
    # print(result)
    raw_signals = []
    for signal in result:
        string = ""
        for chunk in signal:
            string += str(chunk)
        raw_signals.append(string)
    pprint(raw_signals)
