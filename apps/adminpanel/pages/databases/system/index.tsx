import DatabasesPage from 'protolib/bundles/databases/adminPages'
import Head from 'next/head'
import { SiteConfig } from 'app/conf'

export default function Page(props:any) {
  const PageComponent = DatabasesPage['databases'].component
  const projectName = SiteConfig.projectName

  return (
    <>
      <Head>
        <title>{projectName + " - Databases"}</title>
      </Head>
      <PageComponent env="system" {...props} />
    </>
  )
}

export const getServerSideProps = DatabasesPage['databases'].getServerSideProps
