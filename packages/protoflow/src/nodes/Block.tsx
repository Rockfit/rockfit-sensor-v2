import React, { useContext } from 'react';
import { connectItem, dumpConnection, getId, PORT_TYPES, DumpType, createNode } from '../lib/Node';
import Node, { FlowPort, headerSize } from '../Node';
import { useEdges } from 'reactflow';
import { FlowStoreContext } from "../store/FlowsStore";
import { NODE_TREE } from '../toggles';
import { DataOutput } from '../lib/types';
import useTheme, { usePrimaryColor } from '../diagram/Theme';
import { ListOrdered, Square, ArrowDownUp, Plus } from '@tamagui/lucide-icons';
import { generateBoxShadow } from '../lib/shadow';
import { useThemeSetting } from '@tamagui/next-theme'
import { useProtoflow } from '../store/DiagramStore';
import { Button } from '@my/ui';

const blockOffset = 200
const _marginTop = 222
const minBlockHeight = 120
const singleNodeOffset = 100
const alignBlockWithChildrens = true
const _borderWidth = 5


const Block = (node) => {
    const { id, type } = node
    const useFlowsStore = useContext(FlowStoreContext)
    const primaryColor = usePrimaryColor()
    const nodeData = useFlowsStore(state => state.nodeData[id] ?? {})
    const metaData = useFlowsStore(state => state.nodeData[id] && state.nodeData[id]['_metadata'] ? state.nodeData[id]['_metadata'] : { childWidth: 0, childHeight: 0, childHeights: [] })
    const setNodeData = useFlowsStore(state => state.setNodeData)
    const currentPath = useFlowsStore(state => state.currentPath)

    const nodeFontSize = useTheme('nodeFontSize')
    const nodeBackgroundColor = useTheme('nodeBackgroundColor')

    const { resolvedTheme } = useThemeSetting()
    const { setEdges, getEdges } = useProtoflow()


    const isEmpty = !metaData.childHeight
    const marginTop = _marginTop + (useTheme('nodeFontSize') / 2)
    //console.log('metadata in', node.id, metaData)
    const getBlockHeight = () => {
        if (!metaData.childHeight) return minBlockHeight
        return (metaData.childHeight + (marginTop * 1.5)) + ((Math.max(0, nodeData.connections?.length - 1)) * 1)
    }

    const height = id ? getBlockHeight() : 0
    const edges = useEdges();

    const addConnection = () => {
        setNodeData(id, {
            ...nodeData,
            connections: nodeData.connections ? nodeData.connections.concat([1]) : [1]
        })
    }

    const onSwitchConnection = (index) => {
        const prevIndex = index - 1
        const prevBlock = 'block' + prevIndex
        const currBlock = 'block' + index

        const switchEdge = (targetHandle: string) => {
            if (targetHandle.endsWith(prevBlock)) return targetHandle.replace(prevBlock, currBlock)
            else if (targetHandle.endsWith(currBlock)) return targetHandle.replace(currBlock, prevBlock)
            else return targetHandle
        }

        setEdges(edgs => edgs.map(e => ({ ...e, targetHandle: e.target == id ? switchEdge(e.targetHandle) : e.targetHandle })))
    }

    let extraStyle: any = {}
    extraStyle.minHeight = height + 'px'
    extraStyle.border = 0
    extraStyle.minWidth = type == 'CaseClause' || type == 'DefaultClause' ? '400px' : '200px'

    const containerColor = useTheme('containerColor')
    const typeConf = {
        SourceFile: {
            // icon: Box,
            output: false,
            color: primaryColor,
            title: currentPath.split(/[/\\]/).pop()
        },
        Block: {
            icon: ListOrdered,
            color: resolvedTheme == 'dark' ? primaryColor : '#cccccc88',
            title: 'Block'
        },
        CaseClause: {
            icon: Square,
            color: '#cccccc88',
            title: 'Case Clause'
        },
        DefaultClause: {
            icon: Square,
            color: '#cccccc88',
            title: 'Case Clause'
        }
    }

    const buttonStyle = {
        borderColor: typeConf[type].color,
        borderWidth: 4,
        position: 'absolute',
        backgroundColor: nodeBackgroundColor,
        hoverStyle: {
            borderColor: typeConf[type].color,
        },
        scaleIcon: 1.5,
        padding: "$2",
        left: 20
    }
    const connectedEdges = id ? edges.filter(e => e.target == id) : []

    if (id) {
        React.useEffect(() => {
            if (nodeData.mode != 'json' && (connectedEdges.length == nodeData?.connections?.length || !nodeData?.connections?.length)) {
                addConnection()
            } else {
                //remove connections
                const lastConnected = connectedEdges.reduce((last, current) => {
                    const x = parseInt(current.targetHandle.slice(id.length + 6), 10)
                    return x > last ? x : last
                }, -1)

                // console.log(id, 'prev: ', nodeData?.connections, 'edges: ', connectedEdges, lastConnected, 'should be: ', lastConnected)
                setNodeData(id, {
                    ...nodeData,
                    connections: nodeData.connections.slice(0, lastConnected + 2)
                })
            }

        }, [edges, nodeData?.connections?.length])
    }

    const blockEdgesPos = connectedEdges.map(e => Number(e.targetHandle.split('block')[1]))

    const onAddConnection = (index) => {
        let prevIndex = 0

        const spaceOnTop = blockEdgesPos.filter((pos, i) => pos > i).includes(index)
        const realIndex = spaceOnTop ? index - 1 : index
        blockEdgesPos.splice(realIndex, 0, -1).filter(i => i == 0 || i);
        const newPosArr = blockEdgesPos.map((i, a) => (i >= 0 ? a : undefined)).filter(i => i == 0 || i)


        setEdges(edgs => [
            // sort edges by targetHandle to avoid conflicts
            ...edgs.sort((a,b) => ((Number(a?.targetHandle.split('block')[1])) - Number(b.targetHandle.split('block')[1]))).map(e => {
                if (e.target == id) {
                    e['targetHandle'] = id + '_block' + newPosArr[prevIndex]
                    prevIndex = prevIndex + 1
                }
                return {
                    ...e,
                }
            })
        ]
        )
    }

    const lineColor = "#00000025"
    return (
        <Node
            draggable={type != 'SourceFile'}
            // contentStyle={{borderLeft:borderWidth+'px solid '+borderColor}}
            container={!isEmpty}
            style={extraStyle}
            icon={typeConf[type].icon ?? null}
            node={node}
            output={typeConf[type]['output'] == false ? null : { field: 'value', type: 'output' }}
            isPreview={!id}
            title={typeConf[type].title}
            id={id}
            params={[]}
            color={typeConf[type].color}
            dataOutput={DataOutput.block}>
            {isEmpty ? <div style={{ height: nodeFontSize * 2 + 'px' }}></div> : <>
                <div style={{
                    top: nodeFontSize * 1.90,
                    opacity: 1,
                    pointerEvents: 'none',
                    borderRadius: "0px " + nodeFontSize / 1.3 + "px " + nodeFontSize / 1.3 + "px " + nodeFontSize / 1.3 + 'px', position: 'absolute',
                    width: metaData.childWidth + (metaData.childWidth > 700 ? 100 : 0) + 'px',
                    height: height - headerSize - (nodeFontSize * 2) + 'px',
                    backgroundColor: containerColor,
                    borderLeft: nodeFontSize / 2 + 'px solid ' + typeConf[type].color,
                    boxShadow: generateBoxShadow(1.5)
                }}></div>
            </>}
            <div>
                {/* {nodeData.connections?.map((ele, i) => <FlowPort id={id} type='input' label='' style={{ top: 60 + (i * 60) + 'px' }} handleId={'block' + i} />)} */}
                {nodeData.connections?.map((ele, i) => {
                    let pos = i && metaData && metaData && metaData.childHeight && metaData.childHeights && metaData.childHeights[i - 1] ? metaData.childHeights[i - 1].height : 0
                    pos = pos + (nodeData.connections.length == 1 ? singleNodeOffset : marginTop) - 10

                    const isFirst = i == 0
                    const isLast = i == nodeData.connections.length - 1
                    const isSwitchVisible = !isLast && blockEdgesPos.includes(i) && blockEdgesPos.includes(i + 1)
                    const nextPos = isLast ? pos : (metaData.childHeights[i]?.height + marginTop - 10)
                    const switchPos = isLast ? (pos + 40) : (pos + nextPos) / 2

                    const isAddVisible = isLast && blockEdgesPos.includes(i) || blockEdgesPos.includes(i) && blockEdgesPos.includes(i + 1)

                    return <>
                        {connectedEdges.length > 0 && <div style={{ left: (nodeFontSize / 2 - 1) + 'px', position: 'absolute', top: (pos - (nodeFontSize / 4)) + 'px', width: nodeFontSize + 'px', height: (nodeFontSize / 2) + 'px', backgroundColor: typeConf[type].color }} />}
                        {isSwitchVisible && isAddVisible && <div style={{ left: - nodeFontSize + 'px', position: 'absolute', top: switchPos + 'px', width: nodeFontSize + 'px', height: (nodeFontSize / 2) + 'px', backgroundColor: typeConf[type].color }} />}
                        <FlowPort key={i} id={id} type='input' label='' style={{ left: isEmpty ? '' : (nodeFontSize) + 'px', top: pos + 'px' }} handleId={'block' + i} allowedTypes={["data", "flow"]} />
                        {/*@ts-ignore*/}
                        {isFirst && blockEdgesPos.includes(i) ? <Button
                            {...buttonStyle}
                            onPress={() => onAddConnection(i)}
                            top={singleNodeOffset}
                            icon={<Plus color={typeConf[type].color} />}
                        /> : null}
                        {/*@ts-ignore*/}
                        {isAddVisible ? <Button
                            {...buttonStyle}
                            onPress={() => onAddConnection(i + 1)}
                            top={switchPos - 16}
                            icon={<Plus color={typeConf[type].color} />}
                        /> : null}
                        {/*@ts-ignore*/}
                        {isSwitchVisible && isAddVisible ? <Button
                            {...buttonStyle}
                            onPress={() => onSwitchConnection(i + 1)}
                            top={switchPos - 16}
                            left={-53}
                            icon={<ArrowDownUp color={typeConf[type].color} />}
                        /> : null}
                    </>
                })}
            </div>

            {/* <div style={{position:'absolute', width: metaData.childWidth+'px', height: borderWidth+'px', backgroundColor: borderColor}}></div>
            <div style={{top: height-borderWidth+'px', position:'absolute', width: metaData.childWidth+'px', height: borderWidth+'px', backgroundColor: borderColor}}></div>
            <div style={{top: headerSize-(borderWidth*2)+'px', position:'absolute', left: metaData.childWidth+'px', height: height-headerSize+(borderWidth*2)+'px', width: borderWidth+'px', backgroundColor: borderColor}}></div> */}
        </Node>
    );
}

Block.keywords = ["block", "{}", "CaseClause", 'group']
Block.category = "common"
Block.defaultHandle = PORT_TYPES.flow + 'block0'
Block.getData = (node, data, nodesData, edges, mode) => {
    //connect all children in a line
    const statements = node.getStatements ? node.getStatements() : node.getDeclarations()
    statements.forEach((statement, i) => {
        const item = data[getId(statement)]
        if (!item?.type) console.error('item has no type: ', item)
        if (item?.type == 'node') {
            const targetId = item.value.id
            if (targetId) {
                connectItem(targetId, 'output', node, 'block' + i, data, nodesData, edges, null, [PORT_TYPES.data, PORT_TYPES.flow])
            }
        }
    })

    const connections = node.getStatements()
    return { connections: mode == 'json' && connections.length ? connections : connections.concat([1]), mode: mode }
}
Block.dataOutput = DataOutput.block

Block.dump = (node, nodes, edges, nodesData, metadata = null, enableMarkers = false, dumpType: DumpType = "partial", level = 0, trivia = '') => {
    const data = nodesData[node.id] ?? { connections: [] };
    const connections = data.connections ?? []
    const astNode = data._astNode
    var originalText: string;
    if (astNode) {
        originalText = astNode.getText()
    }
    const spacing = node.type == 'Block' ? "\t" : ""

    let body = connections.map((statement, i) => {
        const valueEdge = edges.find(e => e.targetHandle == node.id + PORT_TYPES.flow + "block" + i && e.source)
        var prefix = ''
        //  if(valueEdge) {
        //     const valueNode = nodes.find(n => n.id == valueEdge.source)

        //  if(valueNode) {
        //      const childAstNode = nodesData[valueNode.id]._astNode
        //      if(childAstNode) {
        //             const childFullText = childAstNode.getFullText()
        //             console.log('childFullText: ', childFullText)
        //             const pos = originalText.indexOf(childFullText)
        //             console.log('childFullText pos: ', pos)
        //             if(pos) {
        //                 prefix = originalText.substring(0, pos)
        //             }
        //             console.log('childFullText prev originalText: ', originalText)
        //             originalText = originalText.substring(pos + childFullText.length)
        //             console.log('childFullText post originalText: ', originalText)
        //      }
        //  }
        // }
        const triviaInfo = {}
        let line = dumpConnection(node, "target", "block" + i, PORT_TYPES.flow, '', edges, nodes, nodesData, metadata, enableMarkers, dumpType, level + 1, triviaInfo)
        //console.log('line is: ', line, 'and trivia is: [', triviaInfo['content']+']')
        prefix = triviaInfo['content'] && triviaInfo['content'].includes("\n") || !i ? '' : "\n" + (line ? spacing.repeat(level > 0 ? level : 0) : '')
        line = line ? prefix + line : null
        return { code: line, trivia: triviaInfo['content'] ?? '' }
    }).filter(l => l.code)


    const blockStartSeparator = body.length && body[0].trivia.includes("\n") ? "" : "\n"
    const value = (node.type == 'Block' ? "{" + blockStartSeparator : '') + body.map(b => b.code + ";").join("") + (node.type == 'Block' ? "\n" + spacing.repeat(Math.max(level - 1, 0)) + "}" : '')
    return value
}

// Block.onCreate = (nodeData, edges, nodeStore) => {
//     //const myEdges = edges.filter(edge => edge.target == nodeData.id)

//     return [nodeData].concat(nodeStore?.connections?.filter(c => !isNaN(c)).reduce((total, current, i) => {
//         const phantomId = 'Phantom_'+generateId()
//         connectItem(phantomId, 'output', nodeData.id, 'block'+i, {}, edges, null, [PORT_TYPES.data, PORT_TYPES.flow])
//         return total.concat(createNode([0, 0], 'PhantomBox', phantomId, null, false, edges, {}))
//     },[]))
// }

Block.filterChildren = (node, childNodeList, edges, nodeDataTable, setNodeData) => {
    if (!NODE_TREE) return childNodeList
    //if(!childNodeList.length || !childNodeList[0].id.startsWith('SourceFile_')) return childNodeList
    const vContainer = createNode([0, 0], "VisualGroup", 'VisualGroup_' + childNodeList[0].id, { visible: false }, false, edges)
    vContainer[0].children = childNodeList

    return vContainer;
}

Block.getWidth = (node) => {
    return 50
}

Block.getPosition = (pos, type) => {
    if (alignBlockWithChildrens) pos.y = pos.y + blockOffset
    return pos
}

Block.getSpacingFactor = () => {
    return { factorX: 1.2, factorY: 1 }
}

export default Block
