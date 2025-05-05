import { Node, NodeOutput, NodeParams, filterObject, restoreObject, getFieldValue, Button } from 'protoflow';
import { useColorFromPalette } from 'protoflow/src/diagram/Theme';
import { Plug } from '@tamagui/lucide-icons';
import React from 'react';
import { Fieldset, SizableText, Spinner, XStack } from 'tamagui';
import { API } from 'protobase'
import { SiteConfig} from '@my/config/dist/AppConfig'

const AutomationNode = ({ node = {}, nodeData = {}, children }: any) => {
    const color = useColorFromPalette(9)
    const [loading, setLoading] = React.useState(false)

    return (
        <Node icon={Plug} node={node} isPreview={!node.id} title='Automation' color={color} id={node.id} skipCustom={true}>
            <NodeParams id={node.id} params={[
                { label: 'Name', field: 'mask-name', type: 'input' },
                { label: 'Description', field: 'mask-description', type: 'input' },
                { label: 'Params', field: 'mask-automationParams', type: 'input' },
                { label: 'Tags', field: 'mask-tags', type: 'input' },
                { label: 'Response', field: 'mask-responseMode', type: 'select', data: ['instant', 'wait', 'manual'], static: true},
            ]} />
            <div style={{height: '30px'}} />
            <NodeOutput id={node.id} type={'input'} label={'Run'} vars={['params']} handleId={'mask-onRun'} />
            <NodeOutput id={node.id} type={'input'} label={'Error'} vars={['err']} handleId={'mask-onError'} />
            
            <div style={{height: '0px'}} />
            <Button label={loading?<Spinner color={color} />:"Run"} onPress={async () => {
                const params = getFieldValue('testparams', nodeData)
                setLoading(true)
                const url ='/api/v1/automations/' + getFieldValue('mask-name', nodeData)+(params ? '?'+params : '')
                await API.get(url)
                setLoading(false)
            }}>
            </Button>
            <div style={{height: '0px'}} />
            <NodeParams id={node.id} params={[{ label: 'Await', field: 'await', type: 'boolean', static: true }]} />
            <NodeParams id={node.id} params={[{ label: 'Params', static: true, field: 'testparams', type: 'input' }]} />
            <div style={{height: '20px'}} />
        </Node>
    )
}

export default {
    id: 'automations.automation',
    type: 'CallExpression',
    category: "automation",
    keywords: ['automation', 'app', 'api'],
    check: (node, nodeData) => {
        return node.type == "CallExpression" && nodeData.to == 'context.automations.automation'
    },
    getComponent: (node, nodeData, children) => <AutomationNode node={node} nodeData={nodeData} children={children} />,
    filterChildren: filterObject({keys: {
            name: 'input',
            description: 'input',
            displayName: 'input',
            automationParams: 'input',
            tags: 'input',
            responseMode: 'input',
            app: 'input',
            onRun: 'output',
            onError: 'output'
    }}),
    restoreChildren: restoreObject({keys: {
        name: 'input',
        description: 'input',
        displayName: 'input',
        automationParams: 'input',
        tags: 'input',
        responseMode: 'input',
        app: 'input',
        onRun: { params: {'param-params': { key: "params"}, 'param-res': { key: "res"}}},
        onError: { params: { 'param-err': { key: "err"}}}
    }}),
    getInitialData: () => {
        return {
            await: true,
            to: 'context.automations.automation',
            "param-1": {
                value: "{}",
                kind: "Identifier"
            },
            "mask-name": {
                value: "",
                kind: "StringLiteral"
            },
            "mask-description": {
                value: "",
                kind: "StringLiteral"
            },
            "mask-displayName": {
                value: "",
                kind: "StringLiteral"
            },
            "mask-responseMode": {
                value: "wait",
                kind: "StringLiteral"
            },
            "mask-app": {
                value: 'app',
                kind: "Identifier"
            },
            "mask-automationParams": {
                value: "null",
                kind: "Identifier"
            },
            "mask-tags": {
                value: "null",
                kind: "Identifier"
            }
        }
    }
}