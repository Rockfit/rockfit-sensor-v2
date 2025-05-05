import DevicesPages from 'protolib/bundles/devices/adminPages'
import Head from 'next/head'
import { SiteConfig } from 'app/conf'

export default function Page(props:any) {
  const PageComponent = DevicesPages['deviceBoards/**'].component
  const projectName = SiteConfig.projectName

  return (
    <>
      <Head>
        <title>{projectName + " - Device Boards"}</title>
      </Head>
      <PageComponent {...props} />
    </>
  )
}
