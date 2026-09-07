class Linker:

    def __init__(self, assembly):
        # Clean up the initial list to remove empty strings and raw newlines
        self.assembly = [line.strip() for line in assembly if line.strip() != ""]
    
    def replace_labels(self):
        locations = {}

        # --- PASS 1: Find pure label positions ---
        instruction_idx = 0
        for line in self.assembly:
            if line.startswith("//"):
                continue

            # If the line ends with a colon, it's a declaration line (e.g., "start_7:")
            if line.endswith(":"):
                clean_label = line.replace(":", "").strip()
                locations[clean_label] = instruction_idx
            else:
                # Only increment for real instructions
                instruction_idx += 1
        
        # --- PASS 2: Filter out the declaration lines ---
        cleaned_assembly = []
        for line in self.assembly:
            if line.endswith(":") or line.startswith("//"):
                continue
            cleaned_assembly.append(line)
        self.assembly = cleaned_assembly
        
        # --- PASS 3: Replace label targets with relative offsets ---
        for i in range(len(self.assembly)):
            line = self.assembly[i]
            if line.startswith("//"):
                continue

            # Split line into tokens to check if a label is sitting inside it
            tokens = line.split()
            for j in range(len(tokens)):
                token = tokens[j]
                # Check if this exact token matches any known label name
                if token in locations:
                    offset = locations[token] - i
                    tokens[j] = str(offset)
            
            # Reconstruct the line back together
            self.assembly[i] = " ".join(tokens)

        # FINAL PASS, replace __ADDR__ with stuff
        for i in range(len(self.assembly)):
            line = self.assembly[i]
            tokens = line.split()
            for j in range(len(tokens)):
                token = tokens[j]
                if token.startswith("__ADDR__"):
                    name = token[8:]
                    if name in locations:
                        tokens[j] = str(locations[name])
            self.assembly[i] = " ".join(tokens)

        return self.assembly