from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
   handle = noesis.register("UDG Model", ".bnc")
   noesis.setHandlerTypeCheck(handle, udg_bnc_TypeCheck)
   noesis.setHandlerLoadModel(handle, udg_bnc_LoadModel)
   return 1

def udg_bnc_TypeCheck(data):
    bs = NoeBitStream(data)
    signature = bs.readUInt()
    
    if signature != 0xFE1265AC:
        return 0
        
    bs.seek(16, 0)
    signature = bs.readUInt()
    if signature != 0x61435350:
        return 0
    
    return 1

def udg_bnc_LoadModel(data, mdlList):
    bs = NoeBitStream(data)
    fileSize = len(data)
   
    bs.readUInt()
    pksigOffset = bs.readUInt()
    if (pksigOffset == 0):
        print("Specified file has no PKSIG")
        return 0
        
    baseOffset = 16
    print("PKSIG offset: {} + {}".format(pksigOffset, baseOffset))
    
    # ----------
    
    bs.seek(4 + baseOffset, 0)
    groupCount = bs.readUByte()
    unkCount_0x12 = bs.readUByte()
    unkCount_0x16 = bs.readUByte()
    print("Group count: {}".format(groupCount))
    print("Unknown (offset: 0x12): {}".format(unkCount_0x12))
    print("Unknown (offset: 0x16): {}".format(unkCount_0x16))
    
    # ----------
    
    bs.seek(112 + baseOffset, 0)
    pscHeaderSize = bs.readUInt()
    
    bs.seek(120 + baseOffset, 0)
    modelNameOffset = bs.readUInt()
    
    bs.seek(modelNameOffset + baseOffset, 0)
    modelName = bs.readString()
    print("Model name: {} (offset: {} + {})".format(modelName, modelNameOffset, baseOffset))
    
    # ----------
    
    bs.seek(104 + baseOffset, 0)
    groupNamesArrayOffset = bs.readUInt()
    
    groupNames = list()
    for i in range(0, groupCount):
        bs.seek(groupNamesArrayOffset + baseOffset + (8 * i), 0)
        nameOffset = bs.readUInt()
        bs.seek(nameOffset + baseOffset)
        groupNames.append(bs.readString())
        
        print("Group name {} (offset: {} + {}): {}".format(i, nameOffset, baseOffset, groupNames[i]))
    
    # ----------
    
    bs.seek(80 + baseOffset, 0)
    unkOffset_0x60 = bs.readUInt()
    
    # ----------
    
    bs.seek(pksigOffset + baseOffset, 0)
    pksig = bs.readUInt()
    
    if pksig != 0xF7A2C5E7:
        print("Invalid PKSIG. Expected '0xF7A2C5E7' but got '0x{0:X}'".format(pksig))
        return 0
        
    # ----------
    
    pksigOffset += baseOffset
    
    bs.seek(pksigOffset + 152, 0)
    vertexDataOffset = bs.readUInt()
    
    bs.seek(pksigOffset + 160, 0)
    vertexDataSize = bs.readUInt()
    
    bs.seek(pksigOffset + 168, 0)
    indexDataOffset = bs.readUInt()
    
    bs.seek(pksigOffset + 176, 0)
    indexDataSize = bs.readUInt()
    
    bs.seek(pksigOffset + 184, 0)
    unkDataOffset_0xB8 = bs.readUInt()
    
    bs.seek(pksigOffset + 192, 0)
    unkDataSize_0xB8 = bs.readUInt()
    
    vertexCount = bs.readUInt()
    indexCount = bs.readUInt()
    
    vertexStride = int(vertexDataSize / vertexCount)
    indexSize = int(indexDataSize / indexCount)
    
    print("### -------------- ###")
    
    print("The following locations are relative to the PKSIG offset ({})".format(pksigOffset))
    
    print("### -------------- ###")
    
    print("Vertex data location: {} (offset: 152 + {})".format(vertexDataOffset, pksigOffset))
    print("Vertex data size: {} (offset: 160 + {})".format(vertexDataSize, pksigOffset))
    print("Index data location: {} (offset: 168 + {})".format(indexDataOffset, pksigOffset))
    print("Index data size: {} (offset: 176 + {})".format(indexDataSize, pksigOffset))
    
    print("### -------------- ###")
    
    print("Vertex count: {} (stride: {})".format(vertexCount, vertexStride))
    print("Index count: {} (size: {})".format(indexCount, indexSize))
    
    # ----------
    
    bs.seek(pksigOffset + 16, 0)
    dispDataSize = bs.readUInt()
    
    bs.seek(pksigOffset + 1944, 0)
    bs.seek(16, 1)
    meshCount = bs.readUInt()
    
    print("Mesh count: {}".format(meshCount))
    
    bs.seek(4, 1)
    meshDescOffset = bs.readUInt()
    bs.seek(meshDescOffset - 8, 1)
    
    meshDescBegin = bs.tell()
    
    # ----------
   
    ctx = rapi.rpgCreateContext()
    
    for i in range(0, meshCount):
        bs.seek(meshDescBegin + (i * 1672) + 12, 0)
        
        print("bs location: {}".format(bs.tell()))
        
        startIndex = bs.readUInt()
        baseVertex = bs.readUInt()
        mesh_indexCount = bs.readUShort()
        
        print("Mesh {} start index: {}".format(i, startIndex))
        print("Mesh {} base vertex: {}".format(i, baseVertex))
        print("Mesh {} index count: {}".format(i, mesh_indexCount))
        
        rapi.rpgSetName("{}_mesh{}".format(modelName, i))
    
        bs.seek(vertexDataOffset + pksigOffset + (baseVertex * vertexStride), 0)
        vertexData = bs.readBytes(vertexDataSize - (baseVertex * vertexStride))
    
        bs.seek(indexDataOffset + pksigOffset + (startIndex * 2), 0)
        indexData = bs.readBytes(indexDataSize - (startIndex * 2))
    
        rapi.rpgBindPositionBufferOfs(vertexData, noesis.RPGEODATA_FLOAT, 72, 0)
        rapi.rpgBindUV1BufferOfs(vertexData, noesis.RPGEODATA_FLOAT, 72, 24)
        rapi.rpgBindColorBufferOfs(vertexData, noesis.RPGEODATA_UBYTE, 72, 32, 4)
        rapi.rpgCommitTriangles(indexData, noesis.RPGEODATA_USHORT, mesh_indexCount, noesis.RPGEO_TRIANGLE, 1)
    
        rapi.rpgClearBufferBinds()
    
    mdl = rapi.rpgConstructModel()
    mdlList.append(mdl)
    
    return 1
