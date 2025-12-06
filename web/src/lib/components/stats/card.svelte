<script lang="ts">
    import * as Card from "$lib/components/ui/card/index.js";

    let {title, content, footer}: { title: string, content: any, footer: string } = $props()

</script>

<Card.Root>
    <Card.Header>
        <Card.Title><p>{title}</p></Card.Title>
    </Card.Header>
    <Card.Content>
        <p class="text-2xl font-extrabold leading-0">{content ?? "Error"}</p>
    </Card.Content>
    <Card.Footer>
        <Card.Description >
            <p>{footer}</p>
        </Card.Description>
    </Card.Footer>
</Card.Root>
