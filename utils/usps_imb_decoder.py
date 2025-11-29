#!/usr/bin/env python3
"""
USPS "Intelligent Mail Barcode" Decoder
Ported from JavaScript to Python
Original JavaScript code license:
You may use this code for any purpose, with no restrictions. However,
there is NO WARRANTY for this code; use it at your own risk. This work
is released under the Creative Commons Zero License.
"""
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# barcode-to-bit permutation tables (constants)
DESC_CHAR = [7,1,9,5,8,0,2,4,6,3,5,8,9,7,3,0,6,1,7,4,6,8,9,2,5,1,7,5,4,3,
             8,7,6,0,2,5,4,9,3,0,1,6,8,2,0,4,5,9,6,7,5,2,6,3,8,5,1,9,8,7,4,0,2,6,3]
DESC_BIT = [4,1024,4096,32,512,2,32,16,8,512,2048,32,1024,2,64,8,16,2,
            1024,1,4,2048,256,64,2,4096,8,256,64,16,16,2048,1,64,2,512,2048,32,8,128,8,
            1024,128,2048,256,4,1024,8,32,256,1,8,4096,2048,256,16,32,2,8,1,128,4096,512,
            256,1024]
ASC_CHAR = [4,0,2,6,3,5,1,9,8,7,1,2,0,6,4,8,2,9,5,3,0,1,3,7,4,6,8,9,2,0,5,
            1,9,4,3,8,6,7,1,2,4,3,9,5,7,8,3,0,2,1,4,0,9,1,7,0,2,4,6,3,7,1,9,5,8]
ASC_BIT = [8,1,256,2048,2,4096,256,2048,1024,64,16,4096,4,128,512,64,128,
          512,4,256,16,1,4096,128,1024,512,1,128,1024,32,128,512,64,256,4,4096,2,16,4,1,
          2,32,16,64,4096,2,1,512,16,128,32,1024,4,64,512,2048,4,4096,64,128,32,2048,1,
          8,4]

# Lookup tables for codewords
ENCODE_TABLE = [0] * 1365  # Will be populated by build_codewords
DECODE_TABLE = [None] * 8192  # Mapping of encoded values to codeword indices
FCS_TABLE = [0] * 8192  # Frame check sequence table

def build_codewords(bits, low, hi):
    """
    Build tables of 13-bit codewords for encoding and decoding.
    """
    # Loop through all possible 13-bit codewords
    for fwd in range(8192):
        # Build reversed codeword and count population of 1-bits
        pop = 0
        rev = 0
        tmp = fwd
        for bit in range(13):
            pop += tmp & 1
            rev = (rev << 1) | (tmp & 1)
            tmp >>= 1
        
        if pop != bits:
            continue
            
        if fwd == rev:
            # Palindromic codes go at the end of the table
            ENCODE_TABLE[hi] = fwd
            DECODE_TABLE[fwd] = hi
            DECODE_TABLE[fwd ^ 8191] = hi
            FCS_TABLE[fwd] = 0
            FCS_TABLE[fwd ^ 8191] = 1
            hi -= 1
        elif fwd < rev:
            # Add forward code to front of table
            ENCODE_TABLE[low] = fwd
            DECODE_TABLE[fwd] = low
            DECODE_TABLE[fwd ^ 8191] = low
            FCS_TABLE[fwd] = 0
            FCS_TABLE[fwd ^ 8191] = 1
            low += 1
            
            # Add reversed code to front of table
            ENCODE_TABLE[low] = rev
            DECODE_TABLE[rev] = low
            DECODE_TABLE[rev ^ 8191] = low
            FCS_TABLE[rev] = 0
            FCS_TABLE[rev ^ 8191] = 1
            low += 1

# Call the build function to initialize the tables
build_codewords(5, 0, 1286)
build_codewords(2, 1287, 1364)

def add(num, add_val):
    """
    Add a value to a multiple-precision number represented as an array of 11-bit words.
    """
    for n in range(len(num) - 1, -1, -1):
        if add_val == 0:
            break
        x = num[n] + add_val
        add_val = x >> 11
        num[n] = x & 0x7ff

def muladd(num, mult, add_val):
    """
    Multiply a multiple-precision number by mult and add add_val.
    """
    for n in range(len(num) - 1, -1, -1):
        x = num[n] * mult + add_val
        add_val = x >> 11
        num[n] = x & 0x7ff

def divmod(num, div):
    """
    Divide a multiple-precision number by div and return remainder.
    """
    mod = 0
    for n in range(len(num)):
        x = num[n] + (mod << 11)
        num[n] = q = x // div
        mod = x - q * div
    return mod

def iszero(num):
    """
    Check if a multiple-precision number is zero.
    """
    for n in range(len(num) - 1, -1, -1):
        if num[n] != 0:
            return False
    return True

def calcfcs(num):
    """
    Calculate 11-bit frame check sequence for an array of 11-bit words.
    """
    fcs = 0x1f0
    for n in range(len(num)):
        fcs ^= num[n]
        for bit in range(11):
            fcs <<= 1
            if fcs & 0x800:
                fcs ^= 0xf35
    return fcs

def clean_str(s):
    """
    Clean a string by removing whitespace and converting to uppercase.
    """
    if s is None:
        return ''
    return s.upper().replace(' ', '')

def isdigits(s, n=None):
    """
    Check if a string contains only digits and optionally has a specific length.
    """
    if not s.isdigit():
        return False
    return not n or len(s) == n

def text_to_chars(barcode, strict=True):
    """
    Convert barcode text to "characters" by applying bit permutation.
    """
    barcode = clean_str(barcode)
    chars = [0] * 10
    
    logger.info(f"Converting barcode text to chars, length: {len(barcode)}")
    
    # Pad the barcode to 65 characters if it's shorter
    if len(barcode) < 65:
        barcode = barcode.ljust(65, 'T')  # Pad with tracker bars
    
    for n in range(65):
        try:
            if n >= len(barcode):
                logger.warning(f"Barcode too short: {len(barcode)}, needed 65")
                break
                
            c = barcode[n]
            if c in 'TS':  # track bar
                pass
            elif c == 'D':  # descending bar
                desc_index = DESC_CHAR[n]
                if 0 <= desc_index < 10:
                    chars[desc_index] |= DESC_BIT[n]
                else:
                    logger.warning(f"DESC_CHAR index out of range at position {n}: {desc_index}")
            elif c == 'A':  # ascending bar
                asc_index = ASC_CHAR[n]
                if 0 <= asc_index < 10:
                    chars[asc_index] |= ASC_BIT[n]
                else:
                    logger.warning(f"ASC_CHAR index out of range at position {n}: {asc_index}")
            elif c == 'F':  # full bar
                desc_index = DESC_CHAR[n]
                asc_index = ASC_CHAR[n]
                if 0 <= desc_index < 10:
                    chars[desc_index] |= DESC_BIT[n]
                else:
                    logger.warning(f"DESC_CHAR index out of range at position {n}: {desc_index}")
                if 0 <= asc_index < 10:
                    chars[asc_index] |= ASC_BIT[n]
                else:
                    logger.warning(f"ASC_CHAR index out of range at position {n}: {asc_index}")
            else:
                if strict:
                    logger.warning(f"Unexpected character at position {n}: {c}")
                    return None
        except IndexError as e:
            logger.error(f"Index error in text_to_chars at position {n}: {str(e)}")
            if strict:
                return None
    
    return chars

def chars_to_text(chars):
    """
    Convert characters to barcode text.
    """
    barcode = ""
    
    for n in range(65):
        try:
            # Get indices with bounds checking
            desc_index = DESC_CHAR[n]
            asc_index = ASC_CHAR[n]
            
            # Ensure indices are within valid range
            if 0 <= desc_index < len(chars) and 0 <= asc_index < len(chars):
                has_desc = chars[desc_index] & DESC_BIT[n]
                has_asc = chars[asc_index] & ASC_BIT[n]
                
                if has_desc:
                    if has_asc:
                        barcode += "F"
                    else:
                        barcode += "D"
                else:
                    if has_asc:
                        barcode += "A"
                    else:
                        barcode += "T"
            else:
                # If indices are out of range, use tracker bar as default
                logger.warning(f"Invalid index at position {n}: DESC={desc_index}, ASC={asc_index}")
                barcode += "T"
        except IndexError as e:
            logger.error(f"Index error in chars_to_text at position {n}: {str(e)}")
            barcode += "T"  # Use tracker bar as fallback
    
    return barcode

def decode_chars(chars):
    """
    Decode characters to codewords.
    This is the core of the barcode processing.
    """
    if not chars:
        return None
        
    cw = [0] * 10
    fcs = 0
    
    # Decode characters to codewords
    for n in range(10):
        char_value = chars[n]
        # Safely check if char_value is valid for DECODE_TABLE
        if char_value < 0 or char_value >= len(DECODE_TABLE) or DECODE_TABLE[char_value] is None:
            logger.info(f"Invalid character value at position {n}: {char_value}")
            return None
        cw[n] = DECODE_TABLE[char_value]
        fcs |= FCS_TABLE[char_value] << n
    
    # Validate codewords
    if cw[0] > 1317 or cw[9] > 1270:
        return None
        
    if cw[9] & 1:
        # If the barcode is upside down, cw[9] will always be odd
        return None
        
    cw[9] >>= 1
    if cw[0] > 658:
        cw[0] -= 659
        fcs |= 1 << 10
    
    # Convert codewords to binary
    num = [0, 0, 0, 0, 0, 0, 0, 0, 0, cw[0]]
    
    for n in range(1, 9):
        muladd(num, 1365, cw[n])
    muladd(num, 636, cw[9])
    
    if calcfcs(num) != fcs:
        return None
    
    # Decode tracking information
    track = [0] * 20
    for n in range(19, 1, -1):
        track[n] = divmod(num, 10)
    track[1] = divmod(num, 5)
    track[0] = divmod(num, 10)
    
    # Decode routing information (ZIP code, etc.)
    route = [0] * 11
    pos = 11
    sz = 0
    
    for sz in range(5, 1, -1):
        if sz == 3:
            continue
        if iszero(num):
            break
        add(num, -1)
        for n in range(sz):
            pos -= 1
            route[pos] = divmod(num, 10)
    
    # Ensure sz is defined even if the loop doesn't run
    if 'sz' in locals() and sz < 2 and not iszero(num):
        return None
    
    # Format the results
    result = {}
    result['barcode_id'] = ''.join(str(d) for d in track[0:2])
    result['service_type'] = ''.join(str(d) for d in track[2:5])
    
    if track[5] == 9:
        result['mailer_id'] = ''.join(str(d) for d in track[5:14])
        result['serial_num'] = ''.join(str(d) for d in track[14:20])
    else:
        result['mailer_id'] = ''.join(str(d) for d in track[5:11])
        result['serial_num'] = ''.join(str(d) for d in track[11:20])
    
    if pos <= 6:
        result['zip'] = ''.join(str(d) for d in route[pos:pos+5])
    if pos <= 2:
        result['plus4'] = ''.join(str(d) for d in route[pos+5:pos+9])
    if pos == 0:
        result['delivery_pt'] = ''.join(str(d) for d in route[9:11])
    
    return result

def try_repair(possible, chars, pos):
    """
    Try to repair damaged barcode characters using possible combinations.
    """
    inf = None
    p = possible[pos]
    
    for n in range(len(p)):
        chars[pos] = p[n]
        if pos < 9:
            newinf = try_repair(possible, chars, pos+1)
        else:
            newinf = decode_chars(chars)
            if newinf:
                newinf['suggest'] = chars_to_text(chars)
                newinf['message'] = "Repaired damaged barcode"
                
        if newinf:
            # Abort if multiple solutions are found
            if inf:
                return {"message": "Invalid barcode - multiple solutions found"}
            inf = newinf
    
    return inf

def repair_chars(chars):
    """
    Attempt to repair damaged barcode characters.
    """
    possible = []
    prod = 1
    
    for n in range(10):
        possible.append([])
        c = chars[n]
        
        # Safely check if c is in DECODE_TABLE
        if c < 0 or c >= len(DECODE_TABLE) or DECODE_TABLE[c] is None:
            # Try flipping each bit to see if we get a valid character
            for bit in range(13):
                d = c ^ (1 << bit)  # Flip one bit
                # Safely check d is valid for DECODE_TABLE
                if 0 <= d < len(DECODE_TABLE) and DECODE_TABLE[d] is not None:
                    possible[n].append(d)
        else:
            possible[n].append(c)
            
        # Don't let the number of combinations get too high
        prod *= len(possible[n])
        if prod == 0 or prod > 1000:
            return None
    
    # Create new array for holding repaired characters
    newchars = [0] * 10
    return try_repair(possible, newchars, 0)

def flip_barcode(barcode):
    """
    Flip a barcode upside down (reverse it and swap A/D).
    """
    flipped = ""
    for c in reversed(barcode):
        if c == "A":
            flipped += "D"
        elif c == "D":
            flipped += "A"
        else:
            flipped += c
    return flipped

def repair_barcode(barcode):
    """
    Repair a barcode that might be missing or have an extra character.
    """
    if len(barcode) == 64:
        longer = True  # Missing a character
    elif len(barcode) == 66:
        longer = False  # Extra character
    else:
        return barcode  # Nothing to repair
        
    best = barcode
    besterrs = 5  # Don't try to repair if we can't get more than 5 right
    
    # Try inserting or removing at each position
    for pos in range(66):
        if longer:
            # Insert a dummy character
            testcode = barcode[:pos] + "X" + barcode[pos:]
        else:
            # Remove a character
            testcode = barcode[:pos] + barcode[pos+1:]
            
        chars = text_to_chars(testcode, False)
        if not chars:
            continue  # Skip if we can't convert to chars
            
        errs = 0
        
        for n in range(10):
            char_value = chars[n]
            # First check if the index is valid for DECODE_TABLE
            if char_value < 0 or char_value >= len(DECODE_TABLE) or DECODE_TABLE[char_value] is None:
                errs += 1
                
        if errs < besterrs:
            besterrs = errs
            best = testcode
            
    return best

def decode_barcode(barcode):
    """
    Decode a USPS Intelligent Mail Barcode.
    
    Args:
        barcode: A 65-character string consisting of 'A', 'D', 'T', and 'F'
                 representing the Ascending, Descending, Tracker, and Full bars.
                 
    Returns:
        A dictionary containing decoded fields, or {"message": "error message"} if decoding failed.
    """
    if not barcode:
        logger.warning("Empty barcode provided")
        return {"message": "Empty barcode provided"}

    barcode = clean_str(barcode)
    logger.info(f"Processing barcode: {barcode}")
    
    # First try direct decoding if it's 65 characters
    if len(barcode) == 65:
        logger.info("Attempting direct decode of 65-character barcode")
        chars = text_to_chars(barcode, True)
        if chars:
            decoded = decode_chars(chars)
            if decoded:
                logger.info(f"Successfully decoded: {decoded}")
                # Successfully decoded without errors
                return decoded
            else:
                logger.info("Direct decode failed at decode_chars stage")
        else:
            logger.info("Direct decode failed at text_to_chars stage")
    else:
        logger.info(f"Barcode length {len(barcode)} is not 65 characters")
    
    # Try to repair the barcode if it's not 65 characters
    barcode = repair_barcode(barcode)
    if len(barcode) != 65:
        # Still not 65 characters, can't decode
        logger.warning(f"Repair failed: length still not 65 ({len(barcode)})")
        return {"message": "Barcode must be 65 characters long"}
    else:
        logger.info(f"Repaired to: {barcode}")
    
    # Try with the repaired barcode
    logger.info("Attempting repair of damaged characters")
    chars = text_to_chars(barcode, False)
    if chars:
        inf = repair_chars(chars)
        if inf:
            logger.info(f"Successfully decoded after character repair: {inf}")
            # If we have a suggestion, add highlighting information
            if 'suggest' in inf:
                # Find differences between original and suggested barcode
                # Store as string to avoid type conflicts
                differences = ""
                for i in range(min(len(barcode), len(inf['suggest']))):
                    if barcode[i] != inf['suggest'][i]:
                        differences += f"{i},"
                
                # Store without trailing comma if any differences found
                if differences:
                    inf['highlight_indices'] = differences[:-1]
                else:
                    inf['highlight_indices'] = ""
            return inf
        logger.info("Character repair failed")
    else:
        logger.info("Failed to convert repaired barcode to chars")
    
    # Try flipping the barcode (upside down)
    logger.info("Attempting to flip barcode and decode")
    flipped = flip_barcode(barcode)
    chars = text_to_chars(flipped, False)
    if chars:
        inf = repair_chars(chars)
        if inf and 'barcode_id' in inf:
            inf['message'] = "Barcode seems to be upside down"
            logger.info(f"Successfully decoded flipped barcode: {inf}")
            return inf
        logger.info("Failed to decode flipped barcode")
    else:
        logger.info("Failed to convert flipped barcode to chars")
    
    # Could not decode the barcode
    logger.warning("All decoding attempts failed")
    return {"message": "Invalid barcode"}

def extract_zip_from_imb(imb_code):
    """
    Extract ZIP code from an IMB barcode string.
    
    Args:
        imb_code: A 65-character IMB code string
        
    Returns:
        ZIP code string or None if extraction failed
    """
    decoded = decode_barcode(imb_code)
    
    # Check if we got a successful decode (with ZIP) or an error message
    if decoded and isinstance(decoded, dict):
        if 'zip' in decoded:
            # If we have plus4, include it in the result
            if 'plus4' in decoded:
                return f"{decoded['zip']}-{decoded['plus4']}"
            return decoded['zip']
        elif 'message' in decoded:
            # This is an error message, log it
            logger.warning(f"Decode error: {decoded['message']}")
    
    return None