import { Input, InputProps, ListItem, YGroup, YStack } from "@my/ui"
import { useEffect, useRef, useState } from "react"
import { API } from 'protobase'

type SearchAndSelectProps = {
    getDisplayField?: Function
    maxResults?: number
    options?: string[] | Function
    onSelectItem?: Function
    selectedItem?: any
}

/*

<SearchAndSelect 
    bc="$backgroundTransparent" 
    width={300} 
    // options={["John", "Doe", "Jane", "Smith"]}
    getDisplayField={(item) => item.name}
    dataSource="/api/v1/contacts"
    onSelectItem={(item) => console.log(item)}
    selectedItem={{name: 'john doe', id: '202405-280015-24795-8a309e6c'}}
/>

*/

export const SearchAndSelect = (props: InputProps & SearchAndSelectProps) => {
    const { maxResults, options, getDisplayField, onSelectItem, selectedItem, ...inputProps } = props

    const [search, setSearch] = useState('')
    const [open, setOpen] = useState(false)
    const [results, setResults] = useState(Array.isArray(options) ? options : [])
    const inputRef = useRef(null)
    const [width, setWidth] = useState(0)
    const [selected, setSelected] = useState<string | undefined>(selectedItem)
    const isClickingInOption = useRef(false)

    //const url = dataSource + (search ? '?search=' + search + (maxResults ? '&itemsPerPage=' + maxResults : '') : '')

    const doSearch = async () => {
        if (Array.isArray(options)) {
            setResults(options.filter(option => option.includes(search)))
        } else if(typeof options === 'function') {
            const results = await options(search)
            setResults(results)   
        }
    }

    useEffect(() => { doSearch() }, [search])

    useEffect(() => {
        const input = inputRef.current
        setWidth(input.offsetWidth)
    }, [])

    let searchStr

    if (open) {
        searchStr = search
    } else {
        searchStr = getDisplayField && selected !== undefined ? getDisplayField(selected) : selected
    }

    return (
        <>
            <Input
                ref={inputRef}
                onBlur={(e) => { if (!isClickingInOption.current) setOpen(false) }}
                onFocus={() => { isClickingInOption.current = false; setOpen(true) }}
                onChangeText={setSearch}
                value={searchStr}
                {...inputProps}
            />
            <YStack>
                {/* @ts-ignore */}
                {open && <YGroup pb={0} bc="$bgContent" zIndex={99999999} overflow="auto" maxHeight={300} width={width} position="absolute" alignSelf="center" bordered size="$4">
                    {results.length === 0 && <ListItem>No results</ListItem>}
                    {results.map((item, i) => <YGroup.Item key={i}>
                        <ListItem onPointerDown={() => isClickingInOption.current = true} pressTheme hoverTheme onPress={() => {
                            onSelectItem && onSelectItem(item)
                            setSelected(item)
                            setOpen(false)
                        }}>
                            {getDisplayField ? getDisplayField(item) : item}
                        </ListItem>
                    </YGroup.Item>)}
                </YGroup>}

            </YStack>
        </>

    )
}