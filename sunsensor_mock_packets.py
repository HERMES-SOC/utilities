import struct

num_packets = 10
SS_VECTORCOLL_TLM_MID = 0x08E2
PACKET_ID = int("0001100000000000", 2) + SS_VECTORCOLL_TLM_MID
NUM_VECTORS = 20  # the correct number of vectors is 20
PACKET_LENGTH = NUM_VECTORS * 10 + 15  # 15 bytes for the header including ccsds and 10 bytes per vector

packet = b""

for i in range(num_packets):
    packet_num = i
    ccsds_header = struct.pack(">HHH", PACKET_ID, i, PACKET_LENGTH)
    seconds = i
    subsecs = 0
    ccsds_sec_header = struct.pack(">IH", seconds, subsecs)

    # header
    # h 16 int NumVectorsContained
    # h 16 int VectorPollInterval
    # H 16 uint Temperature
    # I 32 ProcessingTime

    NumVectorsContained = 20
    VectorPollInterval = 0
    Temperature = 25
    ProcessingTime = 1000
    this_packet = (
        ccsds_header
        + ccsds_sec_header
        + struct.pack(">hhH", NumVectorsContained, VectorPollInterval, Temperature)
    )
    this_packet += struct.pack(">I", ProcessingTime)
    
    # The vector payload
    # repeat the following NUM_VECTOR times
    # h 16 INT X_Int<%=sprintf("_%02d",index)%>
    # h 16 INT Y_Int<%= sprintf("_%02d",index) %>
    # h 16 INT Z_Int<%= sprintf("_%02d",index) %>
    # b 8 INT Fit_Quality<%= sprintf("_%02d",index) %>
    # b 8 INT Geometry_Quality<%= sprintf("_%02d",index) %>
    # B 8 UINT Validity<%= sprintf("_%02d",index) %>  0xfc for green, 0xf8 for yellow
    # B 8 UINT BYTEFILLER

    for i in range(NUM_VECTORS):
        this_packet += struct.pack(">hhhbbBB", i, i, i, 1, 2, 0xFC, 4)
    packet += this_packet


print(len(packet))

f = open("sunsensor.bin", "wb")
f.write(packet)
f.close()


import ccsdspy
from ccsdspy import PacketField

# pkt = ccsdspy.FixedLength.from_file("sunsensor_tlm.csv")
import numpy as np

fields = {
    "SECONDS": ["uint", 32],
    "SUBSECONDS": ["uint", 16],
    "NumVectorsContained": ["int", 16],
    "VectorPollInterval": ["int", 16],
    "Temperature": ["uint", 16],
    "ProcessingTime": ["uint", 32],
}

for i in range(NUM_VECTORS):
    fields.update({f"X_INT_{i:02}": ["int", 16]})
    fields.update({f"Y_INT_{i:02}": ["int", 16]})
    fields.update({f"Z_INT_{i:02}": ["int", 16]})
    fields.update({f"FIT_QUALITY_{i:02}": ["int", 8]})
    fields.update({f"GEOMETRY_QUALITY_{i:02}": ["int", 8]})
    fields.update({f"VALIDITY_{i:02}": ["uint", 8]})
    fields.update({f"BYTEFILLER_{i:02}": ["uint", 8]})

packet_fields = [
    PacketField(name=this_name, data_type=result[0], bit_length=result[1])
    for this_name, result in fields.items()
]

pkt = ccsdspy.FixedLength(packet_fields)

result = pkt.load("sunsensor.bin", include_primary_header=True)

print(result)

num_packets = len(result["SECONDS"])
time = (
    result["SECONDS"] + result["SUBSECONDS"] / 1000.0
)  # assume that subseconds are milliseconds
vector_data = np.zeros((3, NUM_VECTORS, num_packets), dtype='uint16')
metadata_int = np.zeros((2, NUM_VECTORS, num_packets), dtype='int8')
metadata_uint = np.zeros((2, NUM_VECTORS, num_packets), dtype='uint8')

for i in range(num_packets):
    vector_data[0, :, i] = [result[f"X_INT_{j:02}"][i] for j in range(NUM_VECTORS)]
    vector_data[1, :, i] = [result[f"Y_INT_{j:02}"][i] for j in range(NUM_VECTORS)]
    vector_data[2, :, i] = [result[f"Z_INT_{j:02}"][i] for j in range(NUM_VECTORS)]
    metadata_int[0, :, i] = [result[f"FIT_QUALITY_{j:02}"][i] for j in range(NUM_VECTORS)]
    metadata_int[1, :, i] = [result[f"GEOMETRY_QUALITY_{j:02}"][i] for j in range(NUM_VECTORS)]
    metadata_uint[0, :, i] = [result[f"VALIDITY_{j:02}"][i] for j in range(NUM_VECTORS)]
    metadata_uint[1, :, i] = [result[f"BYTEFILLER_{j:02}"][i] for j in range(NUM_VECTORS)]
