import React, { useState, useEffect } from "react";
import { BookOpen, Tag, Router } from '@tamagui/lucide-icons';
import { AgentsModel, AgentsType } from './agentsSchemas';
import { API } from 'protobase';
import { DataTable2 } from '../../../components/DataTable2';
import { DataView } from '../../../components/DataView';
import { AdminPage } from '../../../components/AdminPage';
import { CardBody } from '../../../components/CardBody';
import { ItemMenu } from '../../../components/ItemMenu';
import { Tinted } from '../../../components/Tinted';
import { Chip } from '../../../components/Chip';
import { z } from 'protobase';
import { Paragraph, Stack, Switch, TextArea, XStack, YStack, Text, Button } from '@my/ui';
import { getPendingResult } from "protobase";
import { Pencil, UploadCloud } from '@tamagui/lucide-icons';
import { usePageParams } from '../../../next';
import { SSR } from '../../../lib/SSR'
import { withSession } from '../../../lib/Session'
import { Subsystems } from '../subsystems/Subsystems'

const agentsIcon = { name: Tag, deviceDefinition: BookOpen }

const sourceUrl = '/api/core/v1/agents'

export default {
  component: ({ pageState, initialItems, itemData, pageSession, extraData }: any) => {
    const { replace } = usePageParams(pageState)
    const [all, setAll] = useState(false)

    const extraMenuActions = []

    return (<AdminPage title="Agents" pageSession={pageSession}>
      <DataView
        entityName="agents"
        defaultView={"grid"}
        key={all ? 'all' : 'filtered'}
        toolBarContent={
          <XStack mr={"$2"} f={1} space="$1.5" ai="center" jc='flex-end'>
            <Text fontSize={14} color="$color11">
              View all
            </Text>
            <Tinted>
              <Switch
                forceStyle='hover'
                checked={all}
                onCheckedChange={v => setAll(v)} size="$1"
              >
                {/** @ts-ignore */}
                <Switch.Thumb animation="quick" backgroundColor={"$color9"} />
              </Switch>
            </Tinted>


          </XStack>
        }
        itemData={itemData}
        rowIcon={Router}
        sourceUrl={sourceUrl}
        initialItems={initialItems}
        name="agent"
        columns={DataTable2.columns(
          DataTable2.column("name", row => row.name, "name"),
          DataTable2.column("platform", row => row.platform, "platform"),
        )}
        model={AgentsModel}
        pageState={pageState}
        icons={agentsIcon}
        dataTableGridProps={{
          disableItemSelection: true,
          onSelectItem: (item) => { },
          getBody: (data: AgentsType) => <AgentCard data={data} extraMenuActions={extraMenuActions} />
        }}
        extraMenuActions={extraMenuActions}
      />
    </AdminPage>)
  },
  getServerSideProps: SSR(async (context) => withSession(context, ['admin']))
}

type status = {
  online: boolean,
  last_view: string | null
}

const AgentCard = ({ data, extraMenuActions }) => {
  const [status, setStatus] = useState<status>({
    online: false,
    last_view: null
  })

  useEffect(() => {
    const setNewStatus = async () => {
      const statusResult = await getAgentStatus(data.name)
      setStatus(statusResult.status)
    }

    setNewStatus()
    const interval = setInterval(setNewStatus, 5000)

    return () => clearInterval(interval)
  }, [])

  const getAgentStatus = async (agentName) => {
    const response = await API.get(`${sourceUrl}/${agentName}/status`)
    if (!response.data) return {
      online: false,
    }

    return response.data
  }

  function formatTimestamp(timestamp) {
    if (timestamp === null) return "never connected"
    const date = new Date(timestamp);

    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();

    return `${hours}:${minutes} ${day}/${month}/${year}`;
  }

  return <CardBody title={data.name}>
    <XStack right={20} top={20} position={"absolute"}>
      <ItemMenu type="item" sourceUrl={sourceUrl} onDelete={async (sourceUrl, deviceId?: string) => {
        await API.get(`${sourceUrl}/${deviceId}/delete`)
      }} deleteable={() => true} element={AgentsModel.load(data)} extraMenuActions={extraMenuActions} />
    </XStack>
    <XStack paddingInline={20} gap="$3">
      <YStack h="$1" w="$1" bg={status.online ? "$color9" : "$color4"} borderRadius="100%" />
      <Paragraph size={20}>{status.online ? 'online' : 'offline'}</Paragraph>
      <Paragraph size={20} color={"$gray10"}>{formatTimestamp(status.last_view)}</Paragraph>
    </XStack>
    <YStack f={1}>
      {
        Object.keys(data.subsystems ?? {}).length
          ? <Subsystems name={data.name} subsystems={data.subsystems} type={"agent"} />
          : <Paragraph mt="20px" ml="20px" size={20}>{'No subsystems defined'}</Paragraph>
      }
    </YStack>
  </CardBody>

}